import { useState, useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { globalStyles } from './styles/global';
import Svg, { Line, Rect} from 'react-native-svg';
import { getDatabase, ref, onValue } from 'firebase/database';
import { initializeApp } from 'firebase/app';
import * as React from "react";



export default function Parking() {
  const [distance1, setDistance1] = useState("Loading...")
  const [distance2, setDistance2] = useState("Loading...")
  const firebaseConfig = {
  apiKey: "YAIzaSyDMkKHElImfxZRMq0Liy3d31tkjNXqQ03M",
  databaseURL: "https://parking-project-30a86-default-rtdb.firebaseio.com",
};

const app = initializeApp(firebaseConfig);
useEffect(() => {

  const db = getDatabase(app);
  const unSubscribe = onValue(ref(db, '/spots/spot1/distance'), snapshot => {
    const distance1 = snapshot.val();
    setDistance1(distance1)
  });
  return () => unSubscribe();
}, []);

useEffect(() => {

  const db = getDatabase(app);
  const unSubscribe = onValue(ref(db, '/spots/spot2/distance'), snapshot => {
    const distance2 = snapshot.val();
    setDistance2(distance2)
  });
  return () => unSubscribe();
}, []);
  
  return(
    <View >
      <Svg style = {{flex: 1}}>
        <Text style = {{...globalStyles.primaryText, paddingTop:100, fontSize:45}}>Availiability Map</Text>
        <Line x1 = "10" y1 = "200" x2 = "375" y2 = "200" stroke = "black" strokeWidth = "2" />
        {parseInt(distance1, 10) < 30 ? <Rect x = "10" y = "205" height = "90" width = "188" fill = "red"></Rect>:<Rect x = "10" y = "205" height = "90" width = "188" fill = "green"></Rect> }
        <Line x1 = "10" y1 = "300" x2 = "375" y2 = "300" stroke = "black" strokeWidth = "2" />
        {parseInt(distance2, 10) < 30 ? <Rect x = "10" y = "305" height = "90" width = "188" fill = "red"></Rect>:<Rect x = "10" y = "305" height = "90" width = "188" fill = "green"></Rect> }
        <Line x1 = "10" y1 = "400" x2 = "375" y2 = "400" stroke = "black" strokeWidth = "2" />
        {parseInt(distance1, 10) < 30 ? <Rect x = "10" y = "405" height = "90" width = "188" fill = "red"></Rect>:<Rect x = "10" y = "405" height = "90" width = "188" fill = "green"></Rect> }
        <Line x1 = "10" y1 = "500" x2 = "375" y2 = "500" stroke = "black" strokeWidth = "2" />
        {parseInt(distance1, 10) < 30 ? <Rect x = "10" y = "505" height = "90" width = "188" fill = "red"></Rect>:<Rect x = "10" y = "505" height = "90" width = "188" fill = "green"></Rect> }
        <Line x1 = "10" y1 = "600" x2 = "375" y2 = "600" stroke = "black" strokeWidth = "2" />
        {parseInt(distance1, 10) < 30 ? <Rect x = "10" y = "605" height = "90" width = "188" fill = "red"></Rect>:<Rect x = "10" y = "605" height = "90" width = "188" fill = "green"></Rect> }
        <Line x1 = "200" y1 = "200" x2 = "200" y2 = "700" stroke = "black" strokeWidth = "2" />
       
      </Svg>
    {/* Parking Lot 1 */}
    </View>
  );
}
