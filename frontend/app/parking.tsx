import { useState, useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { globalStyles } from './styles/global';
import Svg, { Line, Rect} from 'react-native-svg';
import { getDatabase, ref, onValue } from 'firebase/database';
import { initializeApp } from 'firebase/app';
import * as React from "react";



export default function Parking() {
  const [distance, setDistance] = useState("Loading...")
  const firebaseConfig = {
  apiKey: "YAIzaSyDMkKHElImfxZRMq0Liy3d31tkjNXqQ03M",
  databaseURL: "https://parking-project-30a86-default-rtdb.firebaseio.com",
};

const app = initializeApp(firebaseConfig);
useEffect(() => {

  const db = getDatabase(app);
  const unSubscribe = onValue(ref(db, '/spots/spot1/distance'), snapshot => {
    const distance = snapshot.val();
    setDistance(distance)
  });
  return () => unSubscribe();
}, []);
  return(
    <View >
      <Text style = {{fontSize: 30, paddingTop:160}}>{distance}</Text>
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
