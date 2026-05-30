import React, { useRef, useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  Platform,
  Linking,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import * as Location from 'expo-location';

export default function SOSScreen() {
  const router = useRouter();
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const holdProgress = useRef(new Animated.Value(0)).current;
  const [holding, setHolding] = useState(false);
  const [processing, setProcessing] = useState(false);
  const holdTimer = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      if (holdTimer.current) clearTimeout(holdTimer.current);
    };
  }, []);

  const triggerEmergencyCall = async () => {
    setProcessing(true);
    let numberToCall = '112'; // Default general emergency (112)

    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status === 'granted') {
        const fetchLocation = async () => {
          let loc = await Location.getLastKnownPositionAsync({});
          if (!loc) {
            loc = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
          }
          if (loc) {
            const geocode = await Location.reverseGeocodeAsync(loc.coords);
            return geocode;
          }
          return null;
        };

        // Timeout wrapper (max 2.5 seconds) so emergency calls don't hang
        const timeoutPromise = new Promise<null>((_, reject) => setTimeout(() => reject(new Error('timeout')), 2500));
        
        const geocode = await Promise.race([fetchLocation(), timeoutPromise]);
        
        if (geocode && geocode.length > 0) {
          const place = geocode[0];
          const address = [place.street, place.name, place.district, place.subregion].join(' ').toLowerCase();
          
          // Creative routing based on location
          if (address.includes('highway') || address.includes('expressway') || address.includes('nh ') || address.includes('ah ')) {
            numberToCall = '1033'; // Highway Patrol
          } else if (place.country === 'United States') {
            numberToCall = '911'; // US emergency
          } else if (place.country === 'United Kingdom') {
            numberToCall = '999'; // UK emergency
          }
        }
      }
    } catch (e) {
      console.log('Location fetch failed or timed out', e);
    }
    
    setProcessing(false);
    Linking.openURL(`tel:${numberToCall}`);
  };

  const handlePressIn = () => {
    if (processing) return;
    setHolding(true);
    
    // Heartbeat animation
    Animated.loop(
      Animated.sequence([
        Animated.timing(scaleAnim, { toValue: 1.1, duration: 600, useNativeDriver: true }),
        Animated.timing(scaleAnim, { toValue: 1, duration: 600, useNativeDriver: true }),
      ])
    ).start();

    // Progress circle fill animation (3 seconds)
    Animated.timing(holdProgress, {
      toValue: 100,
      duration: 3000,
      useNativeDriver: false,
    }).start();

    holdTimer.current = setTimeout(() => {
      handlePressOut();
      triggerEmergencyCall();
    }, 3000);
  };

  const handlePressOut = () => {
    if (processing) return;
    setHolding(false);
    if (holdTimer.current) clearTimeout(holdTimer.current);
    
    scaleAnim.stopAnimation();
    holdProgress.stopAnimation();
    
    Animated.timing(scaleAnim, { toValue: 1, duration: 200, useNativeDriver: true }).start();
    Animated.timing(holdProgress, { toValue: 0, duration: 200, useNativeDriver: false }).start();
  };

  const call = (number: string) => {
    Linking.openURL(`tel:${number}`);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>

        {/* HEADER */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.closeButton} onPress={() => router.back()}>
            <Ionicons name="close" size={20} color="#9CA3AF" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Roadside help</Text>
          <View style={styles.liveChip}>
            <View style={styles.liveDot} />
            <Text style={styles.liveText}>24/7</Text>
          </View>
        </View>

        {/* SOS BUTTON */}
        <View style={styles.sosSection}>
          <Animated.View style={[styles.sosRipple, { transform: [{ scale: scaleAnim }] }]}>
            <View style={styles.sosRippleInner} />
          </Animated.View>
          
          <Animated.View style={[
            styles.progressRing, 
            { 
              borderColor: holdProgress.interpolate({
                inputRange: [0, 100],
                outputRange: ['rgba(220, 38, 38, 0)', 'rgba(220, 38, 38, 1)']
              })
            }
          ]} />

          <TouchableOpacity
            style={styles.sosButton}
            onPressIn={handlePressIn}
            onPressOut={handlePressOut}
            activeOpacity={0.85}
            disabled={processing}
          >
            {processing ? (
              <ActivityIndicator color="#fff" size="large" />
            ) : (
              <>
                <Text style={styles.sosLabel}>SOS</Text>
                <Text style={styles.sosHint}>{holding ? "HOLDING..." : "HOLD 3 SEC"}</Text>
              </>
            )}
          </TouchableOpacity>
        </View>

        <Text style={styles.sosDesc}>
          Auto-routes to Highway Patrol or General Emergency (112) based on your location.
        </Text>

        {/* EMERGENCY CONTACTS GRID */}
        <View style={styles.emergencyGrid}>
          <TouchableOpacity style={styles.emergencyCard} onPress={() => call('100')}>
            <View style={[styles.emergencyIcon, { backgroundColor: '#1E3A5F' }]}>
              <Ionicons name="headset" size={22} color="#60A5FA" />
            </View>
            <Text style={styles.emergencyTitle}>Police</Text>
            <Text style={styles.emergencyNumber}>100</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.emergencyCard} onPress={() => call('108')}>
            <View style={[styles.emergencyIcon, { backgroundColor: '#14532D' }]}>
              <Ionicons name="medkit" size={22} color="#4ADE80" />
            </View>
            <Text style={styles.emergencyTitle}>Ambulance</Text>
            <Text style={styles.emergencyNumber}>108</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.emergencyCard} onPress={() => call('1033')}>
            <View style={[styles.emergencyIcon, { backgroundColor: '#7C2D12' }]}>
              <Ionicons name="construct" size={22} color="#FB923C" />
            </View>
            <Text style={styles.emergencyTitle}>Highway aid</Text>
            <Text style={styles.emergencyNumber}>1033</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.emergencyCard}>
            <View style={[styles.emergencyIcon, { backgroundColor: '#713F12' }]}>
              <Ionicons name="car" size={22} color="#FCD34D" />
            </View>
            <Text style={styles.emergencyTitle}>Towing</Text>
            <Text style={styles.emergencyNumber}>Find near</Text>
          </TouchableOpacity>
        </View>

      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#111111' },
  container: {
    flex: 1,
    backgroundColor: '#111111',
    paddingHorizontal: 20,
    paddingBottom: 32,
    justifyContent: 'center',
  },

  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 10,
    paddingBottom: 20,
    position: 'absolute',
    top: 10,
    left: 20,
    right: 20,
    zIndex: 10,
  },
  closeButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#1F1F1F',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#F9FAFB',
  },
  liveChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1F1F1F',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
    gap: 5,
    borderWidth: 1,
    borderColor: '#DC2626',
  },
  liveDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#DC2626',
  },
  liveText: { fontSize: 11, fontWeight: '700', color: '#F87171' },

  // SOS Button
  sosSection: {
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 24,
    height: 180,
  },
  sosRipple: {
    position: 'absolute',
    width: 170,
    height: 170,
    borderRadius: 85,
    backgroundColor: 'rgba(185, 28, 28, 0.3)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  sosRippleInner: {
    width: 148,
    height: 148,
    borderRadius: 74,
    backgroundColor: 'rgba(185, 28, 28, 0.4)',
  },
  progressRing: {
    position: 'absolute',
    width: 140,
    height: 140,
    borderRadius: 70,
    borderWidth: 4,
    borderColor: 'transparent',
  },
  sosButton: {
    width: 130,
    height: 130,
    borderRadius: 65,
    backgroundColor: '#B91C1C',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#DC2626',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 20,
    elevation: 12,
  },
  sosLabel: {
    fontSize: 30,
    fontWeight: '900',
    color: '#fff',
    letterSpacing: 2,
  },
  sosHint: {
    fontSize: 10,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.7)',
    letterSpacing: 1.5,
    marginTop: 2,
  },

  // Description
  sosDesc: {
    textAlign: 'center',
    fontSize: 13,
    color: '#6B7280',
    lineHeight: 20,
    marginBottom: 28,
  },

  // Emergency Grid
  emergencyGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 20,
  },
  emergencyCard: {
    width: '47.5%',
    backgroundColor: '#1C1C1C',
    borderRadius: 16,
    padding: 16,
    gap: 8,
    borderWidth: 1,
    borderColor: '#2D2D2D',
  },
  emergencyIcon: {
    width: 44,
    height: 44,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emergencyTitle: { fontSize: 14, fontWeight: '700', color: '#F9FAFB' },
  emergencyNumber: { fontSize: 13, color: '#9CA3AF' },
});
