import os
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np

import torch
import torch.nn as nn

from torch.utils.data import DataLoader, random_split
from torch.utils.data import Dataset

import torchvision.models as models
from torchvision import transforms
from torchvision.datasets import CocoDetection
from torchvision.utils import make_grid

import pytorch_lightning as pl





class CustomDataset(Dataset):
    def __init__(self, data_dir, transform=None, target_transform=None):
        """
        Args:
            data_dir (string): Directory with all the images and masks.
            transform (callable, optional): Optional transform to be applied on a sample.
            target_transform (callable, optional): Optional transform to be applied on the target (mask).
            class_mode (string): 'file' for different mask files per class, 'color' for different colors in a single mask.
            color_mapping (dict): Mapping from color to class if class_mode is 'color'.
        """
        self.data_dir = data_dir
        self.transform = transform
        self.target_transform = target_transform
        self.image_files = [f for f in os.listdir(data_dir) if f.endswith('.jpg')]

    def __len__(self):
        return len(self.image_files)

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()

        img_name = os.path.join(self.data_dir, self.image_files[idx])
        image = Image.open(img_name).convert('RGB')

        # Get all masks for the current image (normally only one, but ready if multiple classes are present)
        masks = []
        for f in os.listdir(self.data_dir):
            #print(f"> current file: {f}")
            if f.startswith(self.image_files[idx].replace('.jpg', '')) and f.endswith('_mask.png'):
                
                mask_path = os.path.join(self.data_dir, f)
                mask = Image.open(mask_path).convert('L')
                # Resize mask to a fixed size 
                mask = mask.resize((256, 256), Image.NEAREST)
                masks.append(np.array(mask))
                
        combined_mask = np.maximum.reduce(masks)
        
        #mask = torch.tensor(combined_mask, dtype=torch.uint8)
        mask = np.array(combined_mask, dtype=np.uint8)
        

        if self.transform:
            image = self.transform(image)
            
        if self.target_transform:
            mask = Image.fromarray(mask)
            mask = self.target_transform(mask)

        return image, mask
    
    
class CustomDataModule(pl.LightningDataModule):
    def __init__(self, data_dir, batch_size=32, train_val_test_split=(0.7, 0.15, 0.15)):
        super().__init__()
        self.data_dir = data_dir
        self.batch_size = batch_size
        self.train_val_test_split = train_val_test_split

    def setup(self, stage=None):
        
       # Define transforms
        transform = transforms.Compose([
            transforms.Resize((256, 256)),  # Resize images to 256x256
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
            ])

        target_transform = transforms.Compose([
            transforms.Resize((256, 256)),  # Resize images to 256x256
            transforms.ToTensor()
            ])

        
        # Load dataset
        self.dataset = CustomDataset(self.data_dir, transform=transform, target_transform=target_transform)
        
        # Split dataset into train, val, and test
        # Calculate split sizes
        train_size = int(self.train_val_test_split[0] * len(self.dataset))
        val_size = int(self.train_val_test_split[1] * len(self.dataset))
        test_size = len(self.dataset) - train_size - val_size
        self.train_data, self.val_data, self.test_data = random_split(self.dataset, [train_size, val_size, test_size])

    def train_dataloader(self):
        return DataLoader(self.train_data, batch_size=self.batch_size, shuffle=True)

    def val_dataloader(self):
        return DataLoader(self.val_data, batch_size=self.batch_size)

    def test_dataloader(self):
        return DataLoader(self.test_data, batch_size=self.batch_size)


#
# Main function
#

if __name__ == "__main__":
    
    
    data_dir_coco = '../../../../0_DATA/IMPTOX/00_Dataset/uFTIR_curated_square.v5-uftir_curated_square_2024-03-14.coco-segmentation/train'
    data_dir_masks = '/mnt/remote/workspaces/thibault.schowing/0_DATA/IMPTOX/00_Dataset/uFTIR_CurSquareSemantic.v1i.png-mask-semantic/train'
    batch_size = 32
    train_val_test_split = (0.6, 0.2, 0.2)


    # Instantiate the CustomDataModule
    data_module = CustomDataModule(data_dir_masks, batch_size = batch_size, train_val_test_split=train_val_test_split)

    # Load datasets
    data_module.setup()

    # Get a few samples from each dataset
    train_samples = [data_module.train_data[i] for i in range(5)]
    val_samples = [data_module.val_data[i] for i in range(5)]
    test_samples = [data_module.test_data[i] for i in range(5)]

    # Visualize a few samples from each dataset
    def visualize_samples(samples, dataset_name):
        fig, axes = plt.subplots(len(samples), 2, figsize=(10, len(samples) * 5))
        for i, (image, mask) in enumerate(samples):
            axes[i, 0].imshow(np.transpose(image.numpy(), (1, 2, 0)))
            axes[i, 0].set_title(f'{dataset_name} Image {i+1}')
            axes[i, 0].axis('off')

            axes[i, 1].imshow(mask.numpy().squeeze(), cmap='gray')
            axes[i, 1].set_title(f'{dataset_name} Mask {i+1}')
            axes[i, 1].axis('off')

        plt.tight_layout()
        plt.show()
        
    # Visualize samples
    visualize_samples(train_samples, 'Train')
    visualize_samples(val_samples, 'Validation')
    visualize_samples(test_samples, 'Test')