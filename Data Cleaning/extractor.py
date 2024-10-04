import os
import pandas as pd
import numpy as np
from scipy.signal import stft, resample, welch
import pywt
from libemg.feature_extractor import FeatureExtractor
from libemg.utils import get_windows

# Define your feature extraction functions and classes here
class Extractor:
    def __init__(self, signal, fs=1):
        self.signal = np.array(signal)
        self.fs = fs  # Sampling frequency

    def instantaneous_median_frequency_and_mean_power_frequency(self, windows, wavelet='cmor', level=2):
        imdf_values = []
        impf_values = []
        for window in windows:
            if window.ndim > 1:
                window = window.flatten()
            scales = np.arange(1, 100)
            coefficients, frequencies = pywt.cwt(window, scales, wavelet, sampling_period=1/self.fs)
            power_spectrum = np.abs(coefficients) ** 2
            weighted_frequencies = frequencies[:, None] * power_spectrum
            power_spectrum_sum = np.sum(power_spectrum, axis=0)
            weighted_frequencies_sum = np.sum(weighted_frequencies, axis=0)
            with np.errstate(divide='ignore', invalid='ignore'):
                impf = np.nan_to_num(weighted_frequencies_sum / power_spectrum_sum)
            impf_value = np.mean(impf)
            imdf_value = np.median(impf)
            imdf_values.append(imdf_value)
            impf_values.append(impf_value)
        return imdf_values, impf_values

def downsample_signal(df, original_frequency, target_frequency):
    resampling_ratio = target_frequency / original_frequency
    new_length = int(len(df) * resampling_ratio)
    resampled_df = resample(df, new_length)
    return resampled_df

class FeatureExtractorCustom:
    def __init__(self, signal, fs):
        self.signal = np.array(signal)
        self.fs = fs

    def average_rectified_value(self, windows):
        features = [np.mean(np.abs(window)) for window in windows]
        return features

    def compute_stft(self, windows):
        stft_results = []
        for window in windows:
            if window.ndim > 1:
                window = window.flatten()
            f_stft, t_stft, Zxx = stft(window, fs=self.fs, nperseg=300, noverlap=150)
            stft_results.append((f_stft, t_stft, Zxx))
        return stft_results

def extract_features_from_stft(stft_results):
    features = []
    for f_stft, t_stft, Zxx in stft_results:
        power_spectrum = np.abs(Zxx)**2
        spectral_centroid = np.sum(f_stft[:, np.newaxis] * power_spectrum, axis=0) / np.sum(power_spectrum, axis=0)
        spectral_bandwidth = np.sqrt(np.sum(((f_stft[:, np.newaxis] - spectral_centroid)**2) * power_spectrum, axis=0) / np.sum(power_spectrum, axis=0))
        features.append(np.concatenate([spectral_centroid, spectral_bandwidth]))
    return np.array(features)

def extract_features1(windows, target_fs):
    fmean = []
    fpsd = []
    for window in windows:
        mean = np.mean(window)
        f, psd = welch(window, fs=target_fs, nperseg=300, noverlap=150)
        fmean.append(mean)
        fpsd.append(np.mean(psd))
    return fmean, fpsd

def replace_outliers_with_mean(dataframe, column_name):
    Q1 = dataframe[column_name].quantile(0.25)
    Q3 = dataframe[column_name].quantile(0.75)
    IQR = Q3 - Q1
    outliers = (dataframe[column_name] < (Q1 - 1.5 * IQR)) | (dataframe[column_name] > (Q3 + 1.5 * IQR))
    mean_non_outliers = dataframe.loc[~outliers, column_name].mean()
    dataframe.loc[outliers, column_name] = mean_non_outliers
    return dataframe

def process_file(file_path, output_dir):
    fs = 2148
    filt_fs = 1000
    window_size = 300
    window_SHift = 150

    df = pd.read_csv(file_path)
    unique_labels = df['Label'].unique()
    dfs = {label: df[df['Label'] == label] for label in unique_labels}

    features_combined = []

    for label, df_label in dfs.items():
        downsampled_signal = df_label['EMG'].values

        windows = get_windows(downsampled_signal, window_size, window_SHift)
        fe = FeatureExtractor()
        feature_list = ['RMS', 'MAV', 'WL', 'ZC', 'MDF', 'MNF', 'MNP', 'SSC']
        features = fe.extract_features(feature_list, windows)

        extractor = Extractor(windows, fs)
        imdf_feature, impf_feature = extractor.instantaneous_median_frequency_and_mean_power_frequency(windows, 'cmor1.5-1.0')

        feature_extractor_custom = FeatureExtractorCustom(windows, fs)
        temp_feature = feature_extractor_custom.average_rectified_value(windows)
        stft_feature = feature_extractor_custom.compute_stft(windows)
        stft_features = extract_features_from_stft(stft_feature)

        stft_feature_names = [f'stft_feature_{i+1}' for i in range(stft_features.shape[1])]
        stft_df = pd.DataFrame(stft_features, columns=stft_feature_names)

        mean, psd = extract_features1(windows, fs)

        data_flat = {key: value.flatten() for key, value in features.items()}
        processed_data = pd.DataFrame(data_flat)

        temp_data = pd.DataFrame({'IMDF': imdf_feature, 'IMPF': impf_feature, 'PSD': psd})
        processed_data = pd.concat([processed_data, temp_data, stft_df], axis=1)
        processed_data['Label'] = label

        features_combined.append(processed_data)

    combined_df = pd.concat(features_combined, axis=0)
    file_name = os.path.basename(file_path).replace(".csv", "_features.csv")
    combined_df.to_csv(os.path.join(output_dir, file_name), index=False)
    print(f'DataFrame saved to: {os.path.join(output_dir, file_name)}')

# Main function to process all files in a folder
def main(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for file_name in os.listdir(input_folder):
        if file_name.endswith(".csv"):
            file_path = os.path.join(input_folder, file_name)
            process_file(file_path, output_folder)

if __name__ == "__main__":
    input_folder = "E:/Semester/Thesis/Software/Example-Applications-main/Darta Cleaning/Gowthami/Agumented Data"  # Replace with your input folder path
    output_folder = "F:/Dataset/Gowthami"  # Replace with your output folder path
    main(input_folder, output_folder)
