import { useState, useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { globalStyles } from './styles/global';
import Svg, { Line, Rect} from 'react-native-svg';

const ESP32_IP = 'http://192.168.12.179'; // replace with your IP

export default function Parking() {
  const [distance, setDistance] = useState(null);
  const [status, setStatus] = useState('Connecting...');

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${ESP32_IP}/data`);
        const json = await res.json();
        setDistance(json.distance);
        setStatus('Live');
      } catch (e) {
        setStatus('Cannot reach ESP32');
      }
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    // <View style={styles.container}>
    //   <Text style={styles.label}>Distance</Text>
    //   <Text style={styles.reading}>
    //     {distance !== null ? `${distance} cm` : '—'}
    //   </Text>
    //   <Text style={styles.status}>{status}</Text>
    // </View>
    <View>
      <Svg style = {{flex: 1}}>
        <Text style = {{...globalStyles.primaryText, paddingTop:100, fontSize:45}}>Availiability Map</Text>
        <Line x1 = "10" y1 = "200" x2 = "375" y2 = "200" stroke = "black" strokeWidth = "2" />
        <Rect x = "10" y = "205" height = "90" width = "188" fill = "red"></Rect>
        <Line x1 = "10" y1 = "300" x2 = "375" y2 = "300" stroke = "black" strokeWidth = "2" />
        <Line x1 = "10" y1 = "400" x2 = "375" y2 = "400" stroke = "black" strokeWidth = "2" />
        <Line x1 = "10" y1 = "500" x2 = "375" y2 = "500" stroke = "black" strokeWidth = "2" />
        <Line x1 = "10" y1 = "600" x2 = "375" y2 = "600" stroke = "black" strokeWidth = "2" />
        <Line x1 = "200" y1 = "200" x2 = "200" y2 = "700" stroke = "black" strokeWidth = "2" />
       
      </Svg>
    {/* Parking Lot 1 */}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#111' },
  label: { fontSize: 20, color: '#aaa', marginBottom: 8 },
  reading: { fontSize: 72, fontWeight: 'bold', color: '#00e5ff' },
  status: { fontSize: 14, color: '#555', marginTop: 16 },
});