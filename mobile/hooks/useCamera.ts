import { useState } from 'react';
import * as ImagePicker from 'expo-image-picker';

export interface CameraState {
  imageUri: string | null;
  base64: string | null;
  isProcessing: boolean;
}

export function useCamera() {
  const [state, setState] = useState<CameraState>({
    imageUri: null,
    base64: null,
    isProcessing: false,
  });

  const clearImage = () => {
    setState({ imageUri: null, base64: null, isProcessing: false });
  };

  const processImageResult = async (result: ImagePicker.ImagePickerResult) => {
    if (!result.canceled && result.assets && result.assets.length > 0) {
      const asset = result.assets[0];
      setState({
        imageUri: asset.uri,
        base64: asset.base64 || null,
        isProcessing: false,
      });
      return asset;
    }
    setState(s => ({ ...s, isProcessing: false }));
    return null;
  };

  const takePhoto = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      alert('Sorry, we need camera permissions to make this work!');
      return null;
    }

    setState(s => ({ ...s, isProcessing: true }));
    try {
      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ['images'],
        allowsEditing: true,
        quality: 0.8,
        base64: true,
      });
      return await processImageResult(result);
    } catch (error) {
      console.error('Error taking photo:', error);
      setState(s => ({ ...s, isProcessing: false }));
      return null;
    }
  };

  const pickFromGallery = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      alert('Sorry, we need camera roll permissions to make this work!');
      return null;
    }

    setState(s => ({ ...s, isProcessing: true }));
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsEditing: true,
        quality: 0.8,
        base64: true,
      });
      return await processImageResult(result);
    } catch (error) {
      console.error('Error picking image:', error);
      setState(s => ({ ...s, isProcessing: false }));
      return null;
    }
  };

  return {
    ...state,
    takePhoto,
    pickFromGallery,
    clearImage,
  };
}
