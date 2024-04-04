# custom_effects.py
"""
This module aims to extend the scipy_effects module of pydub to include
resonance on the *_pass filters.

Of course, you will need to install scipy and pydub for these to work.
"""
from scipy.signal import butter, sosfilt
from pydub.scipy_effects import _mk_butter_filter, eq, _eq
from pydub.utils import register_pydub_effect

def _mk_resonate(cutoff_freq, q=0):
    """
    Create a resonance effect around the given frequency.

    Args:
        freq: The focus frequency for the resonance.
        q: The Q factor of the resonance. Higher Q values produce a narrower peak.
    """
    def resonate_fn(seg):
        # Convert Q factor to bandwidth, adjust this formula as needed
        bandwidth = calculate_bandwidth(cutoff_freq)  # Define this function based on your filter design

        newSeg = seg._eq(focus_freq=cutoff_freq, bandwidth=bandwidth, mode="peak", gain_dB=(q * 16), order=4)
        # newSeg = seg._eq(focus_freq=2000, bandwidth=200, mode="peak", gain_dB=(q * 10), order=4)
        return newSeg
    
    return resonate_fn


@register_pydub_effect
def resonant_low_pass_filter(seg, cutoff_freq, order=5, q=0):
    """
    Apply a resonant low-pass filter to an audio segment.

    Args:
        seg: The audio segment to filter.
        cutoff_freq: The cutoff frequency of the low-pass filter.
        order: The order of the low-pass filter.
        q: The Q factor for the resonance.
    """
    # Apply the low-pass filter
    filter_fn = _mk_butter_filter(cutoff_freq, 'lowpass', order=order)
    newSeg = seg.apply_mono_filter_to_each_channel(filter_fn)

    if q:
      # Apply the resonance
      resonate_fn = _mk_resonate(cutoff_freq, q)
      newSeg = newSeg.apply_mono_filter_to_each_channel(resonate_fn)

    return newSeg
    # return seg

@register_pydub_effect
def resonant_high_pass_filter(seg, cutoff_freq, order=5, q=0):
    """
    Apply a resonant high-pass filter to an audio segment.

    Args:
        seg: The audio segment to filter.
        cutoff_freq: The cutoff frequency of the high-pass filter.
        order: The order of the high-pass filter.
        q: The Q factor for the resonance.
    """
    # Apply the high-pass filter
    filter_fn = _mk_butter_filter(cutoff_freq, 'highpass', order=order)
    newSeg = seg.apply_mono_filter_to_each_channel(filter_fn)

    if q:
      # Apply the resonance
      resonate_fn = _mk_resonate(cutoff_freq, q)
      newSeg = newSeg.apply_mono_filter_to_each_channel(resonate_fn)

    return newSeg
    # return seg

# Additional utility function
def calculate_bandwidth(cutoff_freq, max_freq=22000, max_bandwidth_percent=0.1):
    max_bandwidth = max_freq * max_bandwidth_percent
    # Adjust bandwidth based on cutoff frequency
    # This is a simple linear scaling, you can replace it with a more complex function if needed
    bandwidth = min(max_bandwidth, cutoff_freq * 0.5)
    return bandwidth