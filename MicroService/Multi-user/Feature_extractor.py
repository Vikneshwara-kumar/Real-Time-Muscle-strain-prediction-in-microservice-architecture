import pandas as pd
import matplotlib.pyplot as plt
from libemg.feature_extractor import FeatureExtractor
import matplotlib.pyplot as plt
from libemg.utils import get_windows
import time
import pywt
import numpy as np
from scipy.signal import welch, stft, resample

class Extractor:
    def __init__(self, signal, fs=1):
        self.signal = np.array(signal)
        self.fs = fs  # Sampling frequency

    def downsample(self, df, original_frequency, target_frequency):
        """
        Downsamples the input DataFrame from original_frequency to target_frequency.

        Parameters:
        df (pd.DataFrame): Input DataFrame to be downsampled.
        original_frequency (float): Original frequency of the input data.
        target_frequency (float): Desired downsampled frequency.

        Returns:
        pd.DataFrame: Downsampled DataFrame with a time index.
        """
        try:
            # Calculate the resampling ratio
            resampling_ratio = target_frequency / original_frequency

            # Determine the new length of the resampled signal
            new_length = int(len(df) * resampling_ratio)

            # Resample the signal
            resampled_df = resample(df.values, new_length, axis=0)

            # Create a time index for the downsampled DataFrame
            start_time = pd.Timestamp('2023-01-01')
            resampled_time_index = pd.date_range(start=start_time, periods=new_length, freq=f'{int(1 / target_frequency * 2000)}L')

            # Create a new DataFrame with the resampled data and the time index
            downsampled_df = pd.DataFrame(resampled_df, columns=df.columns, index=resampled_time_index)

            return downsampled_df
        except Exception as e:
            print(f"Error in downsampling: {e}")
            return None

    def instantaneous_median_frequency_and_mean_power_frequency(self, windows, wavelet='cmor', level=2):
        imdf_values = []
        impf_values = []

        for window in windows:
            # Ensure the window is a 1D array for CWT
            if window.ndim > 1:
                window = window.flatten()

            # Generate scales based on the desired level
            scales = np.arange(1, 100)  # Adjust the range according to your needs

            # Perform Continuous Wavelet Transform (CWT) on the current window
            coefficients, frequencies = pywt.cwt(window, scales, wavelet, sampling_period=1/self.fs)
            
            # Calculate the power spectrum (magnitude squared of the complex coefficients)
            power_spectrum = np.abs(coefficients) ** 2

            # Calculate frequency weighted by power spectrum
            weighted_frequencies = frequencies[:, None] * power_spectrum

            # Sum power across all scales at each time point
            power_spectrum_sum = np.sum(power_spectrum, axis=0)
            weighted_frequencies_sum = np.sum(weighted_frequencies, axis=0)

            # Prevent division by zero
            with np.errstate(divide='ignore', invalid='ignore'):
                impf = np.nan_to_num(weighted_frequencies_sum / power_spectrum_sum)

            # Calculate Instantaneous Mean Power Frequency (IMPF)
            impf_value = np.mean(impf)  # Mean of weighted frequencies

            # Calculate Instantaneous Median Frequency (IMDF)
            imdf_value = np.median(impf)  # Median of weighted frequencies

            imdf_values.append(imdf_value)
            impf_values.append(impf_value)

        return imdf_values, impf_values
    
    def compute_PSD(self, windows):
        """
        Computes the Power Spectral Density (PSD) for each window using Welch's method.

        Parameters:
            windows (list of arrays): List of windows of signals.

        Returns:
            list: Mean power spectral density (PSD) for each window.
        """
        fpsd = []

        for window in windows:
            # Compute the power spectral density (PSD) of the window using Welch's method
            f, psd = welch(window, fs=self.fs, nperseg=300)

            # Append the mean of the PSD to the features list
            fpsd.append(np.mean(psd))

        return fpsd
    
    def compute_stft(self, windows):
        """
        Computes the Short-Time Fourier Transform (STFT) and extracts spectral features.

        Parameters:
            windows (list of arrays): List of windows of signals.

        Returns:
            np.ndarray: Array of extracted features from the STFT results.
        """
        stft_results = []
        features = []

        for window in windows:
            # Ensure the window is a 1D array
            if window.ndim > 1:
                window = window.flatten()

            # Short-Time Fourier Transform (STFT)
            f_stft, t_stft, Zxx = stft(window, fs=self.fs, nperseg=300)
            stft_results.append((f_stft, t_stft, Zxx))

        for f_stft, t_stft, Zxx in stft_results:
            # Convert STFT results to power spectrum
            power_spectrum = np.abs(Zxx)**2
            # Spectral centroid
            spectral_centroid = np.sum(f_stft[:, np.newaxis] * power_spectrum, axis=0) / np.sum(power_spectrum, axis=0)
            # Spectral bandwidth
            spectral_bandwidth = np.sqrt(np.sum(((f_stft[:, np.newaxis] - spectral_centroid)**2) * power_spectrum, axis=0) / np.sum(power_spectrum, axis=0))
            # Spectral contrast (simplified)
            spectral_contrast = np.max(power_spectrum, axis=0) - np.min(power_spectrum, axis=0)

            features.append(np.concatenate([spectral_centroid, spectral_bandwidth, spectral_contrast]))

        return np.array(features)
    
    def General_features(self, windows1,feature_list):
        fe = FeatureExtractor()  # Defining the Feature extractor
        features1 = fe.extract_features(feature_list, windows1)

        # Flatten the arrays
        Features = {key: value.flatten() for key, value in features1.items()}
        Features_1 = pd.DataFrame(Features)

        return Features_1
    
class ProcessData:
    def __init__(self, df, FS, fs, window_size, window_shift, feature_list):
        self.df = df
        self.FS = FS
        self.fs = fs
        self.window_size = window_size
        self.window_shift = window_shift
        self.feature_list = feature_list

    def process(self):
        try:
            # Initialize Extractor
            extractor = Extractor(signal=None, fs=self.fs)

            # Downsample the data
            down_sampled_df = extractor.downsample(self.df, self.FS, self.fs)
            if down_sampled_df is None:
                raise ValueError("Downsampling failed.")

            down_sampled_signal = down_sampled_df['EMG'].values
            windows = get_windows(down_sampled_signal, self.window_size, self.window_shift)
            
            # Extract features
            features1 = extractor.General_features(windows, self.feature_list)
            imdf_feature, impf_feature = extractor.instantaneous_median_frequency_and_mean_power_frequency(windows, 'cmor1.5-1.0')
            stft_feature = extractor.compute_stft(windows)
            stft_feature_names = [f'stft_feature_{i+1}' for i in range(stft_feature.shape[1])]
            features2 = pd.DataFrame(stft_feature, columns=stft_feature_names)
            psd = extractor.compute_PSD(windows)
            features3 = pd.DataFrame({'IMDF': imdf_feature, 'IMPF': impf_feature, 'PSD': psd})

            # Concatenate all features into a single DataFrame
            processed_data = pd.concat([features1, features3, features2], axis=1)

            return processed_data
        except Exception as e:
            print(f"Error in processing data: {e}")
            return None

