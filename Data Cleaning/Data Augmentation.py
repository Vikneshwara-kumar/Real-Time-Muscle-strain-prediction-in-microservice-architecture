import pandas as pd
import numpy as np
import os

def read_emg_data(filename):
    """
    Reads EMG data from a CSV file.

    Args:
        filename (str): Path to the CSV file.

    Returns:
        pd.DataFrame: DataFrame containing the EMG data.
    """
    return pd.read_csv(filename)

def add_noise(data, noise_level=0.0001):
    """
    Adds random noise to the data.

    Args:
        data (np.ndarray): Original data.
        noise_level (float): Noise level as a fraction of the data range.

    Returns:
        np.ndarray: Data with added noise.
    """
    noise = np.random.normal(0, noise_level * np.std(data), data.shape)
    return data + noise

def scale_data(data, scaling_factor_range=(0.9, 1.1)):
    """
    Scales the data by a random factor.

    Args:
        data (np.ndarray): Original data.
        scaling_factor_range (tuple): Range of scaling factors.

    Returns:
        np.ndarray: Scaled data.
    """
    scaling_factor = np.random.uniform(*scaling_factor_range)
    return data * scaling_factor

def time_shift(data, shift_range=(-10, 10)):
    """
    Shifts the data in time.

    Args:
        data (np.ndarray): Original data.
        shift_range (tuple): Range of time shifts.

    Returns:
        np.ndarray: Time-shifted data.
    """
    shift = np.random.randint(*shift_range)
    return np.roll(data, shift)

def time_warp(data, warp_range=(0.8, 1.2)):
    """
    Warps the data in time.

    Args:
        data (np.ndarray): Original data.
        warp_range (tuple): Range of time warps.

    Returns:
        np.ndarray: Time-warped data.
    """
    warp_factor = np.random.uniform(*warp_range)
    indices = np.arange(0, len(data))
    new_indices = np.linspace(0, len(data) - 1, int(len(data) * warp_factor))
    return np.interp(indices, new_indices, data)

def flip_data(data):
    """
    Flips the data sequence.

    Args:
        data (np.ndarray): Original data.

    Returns:
        np.ndarray: Flipped data.
    """
    return np.flip(data)

def augment_data(data, num_subjects):
    """
    Generates augmented data for multiple subjects.

    Args:
        data (pd.DataFrame): Original data.
        num_subjects (int): Number of subjects to generate.

    Returns:
        list: List of augmented data DataFrames.
    """
    augmented_data = []
    for _ in range(num_subjects):
        augmented_subject = data.copy()
        emg_signal = data['EMG'].values

        # Apply augmentations
        emg_signal = add_noise(emg_signal)
        emg_signal = scale_data(emg_signal)
        emg_signal = time_shift(emg_signal)

        augmented_subject['EMG'] = emg_signal
        augmented_data.append(augmented_subject)
    return augmented_data

def save_augmented_data(augmented_data, output_dir="E:/Semester/Thesis/Software/Example-Applications-main/Darta Cleaning/Gowthami/Agumented Data"):
    """
    Saves augmented data to CSV files.

    Args:
        augmented_data (list): List of augmented data DataFrames.
        output_dir (str): Directory to save the augmented data files.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for i, data in enumerate(augmented_data):
        filename = os.path.join(output_dir, f"subject_{i+1}.csv")
        data.to_csv(filename, index=False)

# Example usage
if __name__ == "__main__":
    original_filename = "E:/Semester/Thesis/Software/Example-Applications-main/Darta Cleaning/Gowthami/Trial-5.csv"  # Replace with your CSV file path

    emg_data = read_emg_data(original_filename)
    
    augmented_data = augment_data(emg_data, num_subjects=40)
    save_augmented_data(augmented_data)
