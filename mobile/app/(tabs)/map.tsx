import React, { useState, useEffect, useRef } from 'react';
import { StyleSheet, View, Text, ActivityIndicator } from 'react-native';
import MapView, { Polygon, Region } from 'react-native-maps';
import * as Location from 'expo-location';

const BACKEND_URL = process.env.EXPO_PUBLIC_API_URL || "http://192.168.29.11:8000";

interface Zone {
  id: string;
  type: string;
  speedLimit: number | null;
  coordinates: { latitude: number; longitude: number }[];
  activeRules: string;
}

export default function MapScreen() {
  const [location, setLocation] = useState<Location.LocationObject | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [zones, setZones] = useState<Zone[]>([]);
  const [activeZone, setActiveZone] = useState<Zone | null>(null);
  const [loading, setLoading] = useState(true);
  
  const mapRef = useRef<MapView>(null);

  useEffect(() => {
    (async () => {
      let { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        setErrorMsg('Permission to access location was denied');
        return;
      }

      let loc = await Location.getCurrentPositionAsync({});
      setLocation(loc);

      // Fetch zones from backend (Example: TN zones)
      try {
        const response = await fetch(`${BACKEND_URL}/sync/zones?states=TN`);
        const data = await response.json();
        
        if (data && data.features) {
          const parsedZones: Zone[] = data.features.map((f: any, index: number) => {
            // GeoJSON Polygon coordinates are [[[lon, lat], [lon, lat]...]]
            let coords = [];
            if (f.geometry.type === 'Polygon' && f.geometry.coordinates[0]) {
               coords = f.geometry.coordinates[0].map((coord: number[]) => ({
                 latitude: coord[1],
                 longitude: coord[0]
               }));
            }
            return {
              id: f.properties.zone_id || `zone_${index}`,
              type: f.properties.zone_type || 'unknown',
              speedLimit: f.properties.speed_limit_kmh || null,
              coordinates: coords,
              activeRules: f.properties.active_hours ? `Active Hours: ${f.properties.active_hours}` : 'All Rules Active'
            };
          });
          setZones(parsedZones);
        }
      } catch (err) {
        console.error("Error fetching zones:", err);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const getZoneColor = (type: string) => {
    switch(type) {
      case 'school_zone': return 'rgba(255, 204, 0, 0.4)';
      case 'no_horn': return 'rgba(255, 59, 48, 0.4)';
      case 'speed_limit': return 'rgba(0, 122, 255, 0.4)';
      default: return 'rgba(142, 142, 147, 0.4)';
    }
  };

  const getZoneStroke = (type: string) => {
    switch(type) {
      case 'school_zone': return '#FFCC00';
      case 'no_horn': return '#FF3B30';
      case 'speed_limit': return '#007AFF';
      default: return '#8E8E93';
    }
  };

  // Simple bounding box check for demo purposes
  const handleRegionChange = (region: Region) => {
    const center = { lat: region.latitude, lon: region.longitude };
    
    // Find first zone that the center might be in
    let found = null;
    for (const zone of zones) {
      if (zone.coordinates.length > 0) {
        // Quick bounding box check
        const lats = zone.coordinates.map(c => c.latitude);
        const lons = zone.coordinates.map(c => c.longitude);
        const minLat = Math.min(...lats);
        const maxLat = Math.max(...lats);
        const minLon = Math.min(...lons);
        const maxLon = Math.max(...lons);
        
        if (center.lat >= minLat && center.lat <= maxLat && center.lon >= minLon && center.lon <= maxLon) {
          found = zone;
          break;
        }
      }
    }
    setActiveZone(found);
  };

  if (loading || !location) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#d97706" />
        <Text style={styles.loadingText}>Loading Map & Geofences...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <MapView
        ref={mapRef}
        style={styles.map}
        initialRegion={{
          latitude: location.coords.latitude,
          longitude: location.coords.longitude,
          latitudeDelta: 0.0922,
          longitudeDelta: 0.0421,
        }}
        showsUserLocation={true}
        onRegionChangeComplete={handleRegionChange}
      >
        {zones.map(zone => (
          zone.coordinates.length > 0 ? (
            <Polygon
              key={zone.id}
              coordinates={zone.coordinates}
              fillColor={getZoneColor(zone.type)}
              strokeColor={getZoneStroke(zone.type)}
              strokeWidth={2}
            />
          ) : null
        ))}
      </MapView>
      
      {/* Dynamic Rule Panel */}
      <View style={styles.panel}>
        {activeZone ? (
          <>
            <Text style={styles.zoneTitle}>
              {activeZone.type.replace('_', ' ').toUpperCase()}
            </Text>
            {activeZone.speedLimit && (
              <Text style={styles.speedLimit}>Limit: {activeZone.speedLimit} km/h</Text>
            )}
            <Text style={styles.rules}>{activeZone.activeRules}</Text>
          </>
        ) : (
          <Text style={styles.zoneTitle}>General Driving Zone</Text>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  map: {
    width: '100%',
    height: '100%',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FAF8F5',
  },
  loadingText: {
    marginTop: 10,
    color: '#666',
  },
  panel: {
    position: 'absolute',
    bottom: 30,
    left: 20,
    right: 20,
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  zoneTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  speedLimit: {
    fontSize: 16,
    color: '#d97706',
    fontWeight: '600',
    marginTop: 5,
  },
  rules: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
});
