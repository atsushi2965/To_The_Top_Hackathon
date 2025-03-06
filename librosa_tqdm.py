from functools import wraps
from librosa import ParameterError, cache, core, get_fftlib  # 0.10.2.post1
from librosa.filters import get_window, window_sumsquare
from librosa.util import MAX_MEM_BLOCK, expand_to, dtype_c2r, dtype_r2c, fix_length, frame, is_positive_int, pad_center, phasor, tiny, valid_audio
from numpy import abs, allclose, angle, apply_along_axis, arange, asarray, ceil, empty_like, float64, iscomplexobj, mod, pad, pi, prod, round, sqrt, zeros, zeros_like  # gcd as npgcd
# from scipy import signal
# import soxr
from time import get_clock_info
from tqdm.auto import tqdm, trange
from typing import Union
from warnings import warn


RESOLUTION = get_clock_info('time').resolution


@wraps(core.resample)
@cache(level=20)
def resample(y, *, orig_sr, target_sr, res_type='soxr_hq', fix=True, scale=False, axis=-1, **kwargs):
    # First, validate the audio buffer
    valid_audio(y, mono=False)

    if orig_sr == target_sr:
        return y

    ratio = float(target_sr) / orig_sr

    n_samples = int(ceil(y.shape[axis] * ratio))

    # if res_type in ('scipy', 'fft'):
    #     y_hat = signal.resample(y, n_samples, axis=axis)
    # elif res_type == 'polyphase':
    #     if int(orig_sr) != orig_sr or int(target_sr) != target_sr:
    #         raise ParameterError(
    #             'polyphase resampling is only supported for integer-valued sampling rates.'
    #         )

    #     # For polyphase resampling, we need up- and down-sampling ratios
    #     # We can get those from the greatest common divisor of the rates
    #     # as long as the rates are integrable
    #     orig_sr = int(orig_sr)
    #     target_sr = int(target_sr)
    #     gcd = npgcd(orig_sr, target_sr)
    #     y_hat = signal.resample_poly(
    #         y, target_sr // gcd, orig_sr // gcd, axis=axis
    #     )
    # elif res_type in (
    #     'linear',
    #     'zero_order_hold',
    #     'sinc_best',
    #     'sinc_fastest',
    #     'sinc_medium',
    # ):
    import samplerate
    # Use numpy to vectorize the resampler along the target axis
    # This is because samplerate does not support ndim>2 generally.
    y_hat = apply_along_axis(
        samplerate.resample, axis=axis, arr=y, ratio=ratio, converter_type=res_type, verbose=True
    )
    # elif res_type.startswith('soxr'):
    #     # Use numpy to vectorize the resampler along the target axis
    #     # This is because soxr does not support ndim>2 generally.
    #     y_hat = apply_along_axis(
    #         soxr.resample,
    #         axis=axis,
    #         arr=y,
    #         in_rate=orig_sr,
    #         out_rate=target_sr,
    #         quality=res_type,
    #     )
    # else:
    #     import resampy
    #     y_hat = resampy.resample(y, orig_sr, target_sr, filter=res_type, axis=axis)

    if fix:
        y_hat = fix_length(y_hat, size=n_samples, axis=axis, **kwargs)

    if scale:
        y_hat /= sqrt(ratio)

    # Match dtypes
    return asarray(y_hat, dtype=y.dtype)


@wraps(core.stft)
@cache(level=20)
def stft(
    y,
    *,
    n_fft=2048,
    hop_length=None,
    win_length=None,
    window='hann',
    center=True,
    dtype=None,
    pad_mode='constant',
    out=None,
):
    # By default, use the entire frame
    if win_length is None:
        win_length = n_fft

    # Set the default hop, if it's not already specified
    if hop_length is None:
        hop_length = int(win_length // 4)
    elif not is_positive_int(hop_length):
        raise ParameterError(f'hop_length={hop_length} must be a positive integer')

    # Check audio is valid
    valid_audio(y, mono=False)

    fft_window = get_window(window, win_length, fftbins=True)

    # Pad the window out to n_fft size
    fft_window = pad_center(fft_window, size=n_fft)

    # Reshape so that the window can be broadcast
    fft_window = expand_to(fft_window, ndim=1 + y.ndim, axes=-2)

    # Pad the time series so that frames are centered
    if center:
        if pad_mode in ('wrap', 'maximum', 'mean', 'median', 'minimum'):
            # Note: padding with a user-provided function 'works', but
            # use at your own risk.
            # Since we don't pass-through kwargs here, any arguments
            # to a user-provided pad function should be encapsulated
            # by using functools.partial:
            #
            # >>> my_pad_func = functools.partial(pad_func, foo=x, bar=y)
            # >>> librosa.stft(..., pad_mode=my_pad_func)

            raise ParameterError(
                f"pad_mode='{pad_mode}' is not supported by librosa.stft"
            )

        if n_fft > y.shape[-1]:
            warn(
                f'n_fft={n_fft} is too large for input signal of length={y.shape[-1]}'
            )

        # Set up the padding array to be empty, and we'll fix the target dimension later
        padding = [(0, 0) for _ in range(y.ndim)]

        # How many frames depend on left padding?
        start_k = int(ceil(n_fft // 2 / hop_length))

        # What's the first frame that depends on extra right-padding?
        tail_k = (y.shape[-1] + n_fft // 2 - n_fft) // hop_length + 1

        if tail_k <= start_k:
            # If tail and head overlap, then just copy-pad the signal and carry on
            start = 0
            extra = 0
            padding[-1] = (n_fft // 2, n_fft // 2)
            y = pad(y, padding, mode=pad_mode)
        else:
            # If tail and head do not overlap, then we can implement padding on each part separately
            # and avoid a full copy-pad

            # 'Middle' of the signal starts here, and does not depend on head padding
            start = start_k * hop_length - n_fft // 2
            padding[-1] = (n_fft // 2, 0)

            # +1 here is to ensure enough samples to fill the window
            # fixes bug #1567
            y_pre = pad(
                y[..., : (start_k - 1) * hop_length - n_fft // 2 + n_fft + 1],
                padding,
                mode=pad_mode,
            )
            y_frames_pre = frame(y_pre, frame_length=n_fft, hop_length=hop_length)
            # Trim this down to the exact number of frames we should have
            y_frames_pre = y_frames_pre[..., :start_k]

            # How many extra frames do we have from the head?
            extra = y_frames_pre.shape[-1]

            # Determine if we have any frames that will fit inside the tail pad
            if tail_k * hop_length - n_fft // 2 + n_fft <= y.shape[-1] + n_fft // 2:
                padding[-1] = (0, n_fft // 2)
                y_post = pad(
                    y[..., (tail_k) * hop_length - n_fft // 2 :], padding, mode=pad_mode
                )
                y_frames_post = frame(
                    y_post, frame_length=n_fft, hop_length=hop_length
                )
                # How many extra frames do we have from the tail?
                extra += y_frames_post.shape[-1]
            else:
                # In this event, the first frame that touches tail padding would run off
                # the end of the padded array
                # We'll circumvent this by allocating an empty frame buffer for the tail
                # this keeps the subsequent logic simple
                post_shape = list(y_frames_pre.shape)
                post_shape[-1] = 0
                y_frames_post = empty_like(y_frames_pre, shape=post_shape)
    else:
        if n_fft > y.shape[-1]:
            raise ParameterError(
                f'n_fft={n_fft} is too large for uncentered analysis of input signal of length={y.shape[-1]}'
            )

        # 'Middle' of the signal starts at sample 0
        start = 0
        # We have no extra frames
        extra = 0

    fft = get_fftlib()

    if dtype is None:
        dtype = dtype_r2c(y.dtype)

    # Window the time series.
    y_frames = frame(y[..., start:], frame_length=n_fft, hop_length=hop_length)

    # Pre-allocate the STFT matrix
    shape = list(y_frames.shape)

    # This is our frequency dimension
    shape[-2] = 1 + n_fft // 2

    # If there's padding, there will be extra head and tail frames
    shape[-1] += extra

    if out is None:
        stft_matrix = zeros(shape, dtype=dtype, order='F')
    elif not (allclose(out.shape[:-1], shape[:-1]) and out.shape[-1] >= shape[-1]):
        raise ParameterError(
            f'Shape mismatch for provided output array out.shape={out.shape} and target shape={shape}'
        )
    elif not iscomplexobj(out):
        raise ParameterError(f'output with dtype={out.dtype} is not of complex type')
    else:
        if allclose(shape, out.shape):
            stft_matrix = out
        else:
            stft_matrix = out[..., : shape[-1]]

    # Fill in the warm-up
    if center and extra > 0:
        off_start = y_frames_pre.shape[-1]
        stft_matrix[..., :off_start] = fft.rfft(fft_window * y_frames_pre, axis=-2)

        off_end = y_frames_post.shape[-1]
        if off_end > 0:
            stft_matrix[..., -off_end:] = fft.rfft(fft_window * y_frames_post, axis=-2)
    else:
        off_start = 0

    n_columns = int(
        MAX_MEM_BLOCK // (prod(y_frames.shape[:-1]) * y_frames.itemsize)
    )
    n_columns = max(n_columns, 1)

    for bl_s in trange(0, y_frames.shape[-1], n_columns, desc='sft0', mininterval=RESOLUTION, unit='block'):
        bl_t = min(bl_s + n_columns, y_frames.shape[-1])

        stft_matrix[..., bl_s + off_start : bl_t + off_start] = fft.rfft(
            fft_window * y_frames[..., bl_s:bl_t], axis=-2
        )
    return stft_matrix


@wraps(core.istft)
@cache(level=30)
def istft(
    stft_matrix,
    *,
    hop_length=None,
    win_length=None,
    n_fft=None,
    window='hann',
    center=True,
    dtype=None,
    length=None,
    out=None,
):
    if n_fft is None:
        n_fft = 2 * (stft_matrix.shape[-2] - 1)

    # By default, use the entire frame
    if win_length is None:
        win_length = n_fft

    # Set the default hop, if it's not already specified
    if hop_length is None:
        hop_length = int(win_length // 4)

    ifft_window = get_window(window, win_length, fftbins=True)

    # Pad out to match n_fft, and add broadcasting axes
    ifft_window = pad_center(ifft_window, size=n_fft)
    ifft_window = expand_to(ifft_window, ndim=stft_matrix.ndim, axes=-2)

    # For efficiency, trim STFT frames according to signal length if available
    if length:
        if center:
            padded_length = length + 2 * (n_fft // 2)
        else:
            padded_length = length
        n_frames = min(stft_matrix.shape[-1], int(ceil(padded_length / hop_length)))
    else:
        n_frames = stft_matrix.shape[-1]

    if dtype is None:
        dtype = dtype_c2r(stft_matrix.dtype)

    shape = list(stft_matrix.shape[:-2])
    expected_signal_len = n_fft + hop_length * (n_frames - 1)

    if length:
        expected_signal_len = length
    elif center:
        expected_signal_len -= 2 * (n_fft // 2)

    shape.append(expected_signal_len)

    if out is None:
        y = zeros(shape, dtype=dtype)
    elif not allclose(out.shape, shape):
        raise ParameterError(
            f'Shape mismatch for provided output array out.shape={out.shape} != {shape}'
        )
    else:
        y = out
        # Since we'll be doing overlap-add here, this needs to be initialized to zero.
        y.fill(0.0)

    fft = get_fftlib()

    if center:
        # First frame that does not depend on padding
        #  k * hop_length - n_fft//2 >= 0
        # k * hop_length >= n_fft // 2
        # k >= (n_fft//2 / hop_length)

        start_frame = int(ceil((n_fft // 2) / hop_length))

        # Do overlap-add on the head block
        ytmp = ifft_window * fft.irfft(stft_matrix[..., :start_frame], n=n_fft, axis=-2)

        shape[-1] = n_fft + hop_length * (start_frame - 1)
        head_buffer = zeros(shape, dtype=dtype)

        core.spectrum.__overlap_add(head_buffer, ytmp, hop_length)

        # If y is smaller than the head buffer, take everything
        if y.shape[-1] < shape[-1] - n_fft // 2:
            y[..., :] = head_buffer[..., n_fft // 2 : y.shape[-1] + n_fft // 2]
        else:
            # Trim off the first n_fft//2 samples from the head and copy into target buffer
            y[..., : shape[-1] - n_fft // 2] = head_buffer[..., n_fft // 2 :]

        # This offset compensates for any differences between frame alignment
        # and padding truncation
        offset = start_frame * hop_length - n_fft // 2

    else:
        start_frame = 0
        offset = 0

    n_columns = int(
        MAX_MEM_BLOCK // (prod(stft_matrix.shape[:-1]) * stft_matrix.itemsize)
    )
    n_columns = max(n_columns, 1)

    frame = 0
    for bl_s in trange(start_frame, n_frames, n_columns, desc='sft2', mininterval=RESOLUTION, unit='block'):
        bl_t = min(bl_s + n_columns, n_frames)

        # invert the block and apply the window function
        ytmp = ifft_window * fft.irfft(stft_matrix[..., bl_s:bl_t], n=n_fft, axis=-2)

        # Overlap-add the istft block starting at the i'th frame
        core.spectrum.__overlap_add(y[..., frame * hop_length + offset :], ytmp, hop_length)

        frame += bl_t - bl_s

    # Normalize by sum of squared window
    ifft_window_sum = window_sumsquare(
        window=window,
        n_frames=n_frames,
        win_length=win_length,
        n_fft=n_fft,
        hop_length=hop_length,
        dtype=dtype,
    )

    if center:
        start = n_fft // 2
    else:
        start = 0

    ifft_window_sum = fix_length(ifft_window_sum[..., start:], size=y.shape[-1])

    approx_nonzero_indices = ifft_window_sum > tiny(ifft_window_sum)

    y[..., approx_nonzero_indices] /= ifft_window_sum[approx_nonzero_indices]

    return y


@wraps(core.phase_vocoder)
def phase_vocoder(D, *, rate, hop_length=None, n_fft=None):
    if n_fft is None:
        n_fft = 2 * (D.shape[-2] - 1)

    if hop_length is None:
        hop_length = int(n_fft // 4)

    time_steps = arange(0, D.shape[-1], rate, dtype=float64)

    # Create an empty output array
    shape = list(D.shape)
    shape[-1] = len(time_steps)
    d_stretch = zeros_like(D, shape=shape)

    # Expected phase advance in each bin per frame
    phi_advance = hop_length * core.fft_frequencies(sr=2 * pi, n_fft=n_fft)

    # Phase accumulator; initialize to the first sample
    phase_acc = angle(D[..., 0])

    # Pad 0 columns to simplify boundary logic
    padding = [(0, 0) for _ in D.shape]
    padding[-1] = (0, 2)
    D = pad(D, padding, mode='constant')

    for t, step in enumerate(tqdm(time_steps, 'sft1', mininterval=RESOLUTION, unit='frame')):
        columns = D[..., int(step) : int(step + 2)]

        # Weighting for linear magnitude interpolation
        alpha = mod(step, 1.0)
        mag = (1.0 - alpha) * abs(columns[..., 0]) + alpha * abs(columns[..., 1])

        # Store to output array
        d_stretch[..., t] = phasor(phase_acc, mag=mag)

        # Compute phase advance
        dphase = angle(columns[..., 1]) - angle(columns[..., 0]) - phi_advance

        # Wrap to -pi:pi range
        dphase = dphase - 2.0 * pi * round(dphase / (2.0 * pi))

        # Accumulate phase
        phase_acc += phi_advance + dphase

    return d_stretch


class tqrs(tqdm):
    def __init__(self, *args, sr: Union[int, float] = 22050, **kwargs):
        self.sr = sr
        super().__init__(*args, **kwargs)

    @property
    def format_dict(self):
        ret = super().format_dict
        ret['elapsed'] = self.n/self.sr
        ret['rate'] = self.sr
        return ret


core.resample = resample
core.stft = stft
core.istft = istft
core.phase_vocoder = phase_vocoder
