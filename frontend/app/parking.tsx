import { useState, useEffect } from 'react';
import {Modal, View, Text, StyleSheet, Button, Pressable, useWindowDimensions, ScrollView} from 'react-native';
import { globalStyles } from '../components/styles/global';
import Svg, { Line, Rect} from 'react-native-svg';
import { getDatabase, ref, onValue } from 'firebase/database';
import { app } from '../lib/firebase';
import * as React from "react";
import { SafeAreaView } from "react-native-safe-area-context";
import ParkingLotLayout from '../components/ParkingLotLayout';


// 35, 91, 234

export default function Parking() {
  const [distance1, setDistance1] = useState("Loading...")
  const [distance2, setDistance2] = useState("Loading...")
  const [propertiesShown, showProperties] = useState(false)
  const {width, height} = useWindowDimensions();
  // config moved to lib/firebase.ts. it used to be initialised right here in the render body
  // which meant a new initializeApp call every single render - firebase let it slide only
  // because the options were identical every time. the model tab needs projectId for
  // firestore, so once that got added the options stopped matching and this threw
  // "app already exists with different options". one shared app fixes it for good.
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
  <ScrollView>
    <View style = {{flex: 1, alignContent: 'center'}}>
      <View style = {{alignContent: 'center'}}>
        <ParkingLotLayout/>
      </View>
      <Modal transparent={true} visible={propertiesShown}>
        <View style={{ backgroundColor: "#000000aa", flex: 1}}>
          <View style = {{backgroundColor: 'white',margin: 100, borderRadius: 10}}>
            <Text style={{ fontSize: 30, textAlign: "center", marginTop: 100}}>hello</Text>
            <Button title = "Close" onPress={() => {showProperties(false)}}></Button>
          </View>
        </View>
      </Modal>
    {/* Parking Lot 1 */}
    </View>
    </ScrollView>
  );
}
