import React from 'react';
import {useWindowDimensions, Text} from 'react-native';
import Svg, { Path, Defs, Rect, Pattern, Use, Image as SvgImage } from 'react-native-svg';
import parking from '../app/parking'
import { useState, useEffect } from 'react';
import { getDatabase, ref, onValue } from 'firebase/database';
import { app } from '../lib/firebase';
import { getFirestore , onSnapshot, doc} from 'firebase/firestore';
export default function ParkingLotSvg() {
  const [distance1, setDistance1] = useState<boolean | null>(null);
  const [distance2, setDistance2] = useState("Loading...")
  const [propertiesShown, showProperties] = useState(false)
  const {width, height} = useWindowDimensions();
  const scale = width / 2063;
  // config moved to lib/firebase.ts. it used to be initialised right here in the render body
  // which meant a new initializeApp call every single render - firebase let it slide only
  // because the options were identical every time. the model tab needs projectId for
  // firestore, so once that got added the options stopped matching and this threw
  // "app already exists with different options". one shared app fixes it for good.
useEffect(() => {

  const db = getDatabase(app);
  const unSubscribe = onValue(ref(db, '/spots/spot2/distance'), snapshot => {
    const distance2 = snapshot.val();
    setDistance2(distance2)
  });
  return () => unSubscribe();
}, []);

  return (
    <Svg
      width={width}
      height={4600 * scale}
      viewBox="0 0 1500 3000"
    >
      <Text style = {{fontSize: 45, marginTop:135, marginLeft:110}}>
      ॐ Temple
      </Text>
      <Rect x = "300" y = "225" height = "600" width = "1000" fill = "none" stroke = "black" strokeWidth = "5"></Rect>
    {parseInt(distance2, 10) < 30 ? <Rect x = "10" y = "205" height = "90" width = "188" fill = "red"></Rect>:<Rect x = "10" y = "205" height = "90" width = "188" fill = "green"></Rect> }
          <Rect x = "10" y = "410" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "10" y = "555" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "10" y = "695" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "10" y = "835" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "10" y = "975" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "10" y = "1117.5" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "10" y = "1260" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "10" y = "1402.5" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "10" y = "1545" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "10" y = "1687.5" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "10" y = "1830" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "10" y = "1972.5" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "10" y = "2115" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "10" y = "2257.5" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "10" y = "2400" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "10" y = "2542.5" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "10" y = "2685" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "10" y = "2827.5" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "10" y = "2970" height = "120" width = "188" fill = "red"></Rect>






        <Rect x = "475" y = "830" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "475" y = "970" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "475" y = "1105" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "475" y = "1245" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "475" y = "1392.5" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "475" y = "1530" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "475" y = "1670" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "475" y = "1810" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "475" y = "1952.5" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "475" y = "2095" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "475" y = "2237.5" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "475" y = "2380" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "475" y = "2520" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "475" y = "2665" height = "120" width = "188" fill = "red"></Rect>


        <Rect x = "830" y = "830" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "830" y = "970" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "830" y = "1105" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "830" y = "1245" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "830" y = "1392.5" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "830" y = "1530" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "830" y = "1670" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "830" y = "1810" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "830" y = "1952.5" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "830" y = "2095" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "830" y = "2237.5" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "830" y = "2380" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "830" y = "2520" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "830" y = "2665" height = "120" width = "188" fill = "red"></Rect>




        {/* Top Row */}
        <Rect x = "227.5" y = "15" height = "188" width = "120" fill = "red"></Rect>
        <Rect x = "370" y = "15" height = "188" width = "120" fill = "red"></Rect>
        <Rect x = "512.5" y = "15" height = "188" width = "120" fill = "red"></Rect>
        <Rect x = "655" y = "15" height = "188" width = "120" fill = "red"></Rect>
        <Rect x = "797.5" y = "15" height = "188" width = "120" fill = "red"></Rect>


        <Rect x = "1305" y = "1120" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "1305" y = "1255" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "1305" y = "1400" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "1305" y = "1540" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "1305" y = "1690" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "1305" y = "1825" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "1305" y = "1960" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "1305" y = "2102.5" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "1305" y = "2245" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "1305" y = "2387.5" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "1305" y = "2530" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "1305" y = "2672.5" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "1305" y = "2815" height = "120" width = "188" fill = "red"></Rect>
        <Rect x = "1305" y = "2957.5" height = "120" width = "188" fill = "red"></Rect>


      <Path stroke="#000" d="M218 .5h708M218.5 1v204"/>
      <Path stroke="#000" d="M0-.5h204.002" transform="matrix(.00421 1 -1 .00244 356.293 1)"/>
      <Path stroke="#000" d="M489.5 1v204m143-204v204m143-204v204M926 1v204M.5 958V250M1 957.5h204"/>
      <Path stroke="#000" d="M0-.5h204.002" transform="matrix(1 -.00421 .00244 1 1 819.707)"/>
      <Path stroke="#000" d="M1 686.5h204M1 543.5h204M1 400.5h204M1 250h204M.5 1666V958m.5 707.5h204"/>
      <Path stroke="#000" d="M0-.5h204.002" transform="matrix(1 -.00421 .00244 1 1 1527.71)"/>
      <Path stroke="#000" d="M1 1394.5h204m-204-143h204m-204-143h204M1 958h204M.5 2374v-708m.5 707.5h204"/>
      <Path stroke="#000" d="M0-.5h204.002" transform="matrix(1 -.00421 .00244 1 1 2235.71)"/>
      <Path stroke="#000" d="M1 2102.5h204m-204-143h204m-204-143h204M1 1666h204M.5 3082v-708m.5 707.5h204"/>
      <Path stroke="#000" d="M0-.5h204.002" transform="matrix(1 -.00421 .00244 1 1 2943.71)"/>
      <Path stroke="#000" d="M1 2810.5h204m-204-143h204m-204-143h204M1 2374h204m466.5-847v708m-.5-707.5H467"/>
      <Path stroke="#000" d="M0-.5h204.002" transform="matrix(-1 .00421 -.00244 -1 671 1665.29)"/>
      <Path stroke="#000" d="M671 1798.5H467m204 143H467m204 143H467M671 2235H467m204.5-1v557m-.5-556.5H467"/>
      <Path stroke="#000" d="M0-.5h204.002" transform="matrix(-1 .00421 -.00244 -1 671 2372.29)"/>
      <Path stroke="#000" d="M671 2505.5H467m204 143H467m204 143H467M671.5 819v708m-.5-707.5H467"/>
      <Path stroke="#000" d="M0-.5h204.002" transform="matrix(-1 .00421 -.00244 -1 671 957.293)"/>
      <Path stroke="#000" d="M671 1090.5H467m204 143H467m204 143H467M671 1527H467m1034.5 290v708m-.5-707.5h-204"/>
      <Path stroke="#000" d="M0-.5h204.002" transform="matrix(-1 .00421 -.00244 -1 1501 1955.29)"/>
      <Path stroke="#000" d="M1501 2088.5h-204m204 143h-204m204 143h-204m204 150.5h-204m204.5-1v557m-.5-556.5h-204"/>
      <Path stroke="#000" d="M0-.5h204.002" transform="matrix(-1 .00421 -.00244 -1 1501 2662.29)"/>
      <Path stroke="#000" d="M1501 2795.5h-204m204 143h-204m204 143h-204M1501.5 1109v708m-.5-707.5h-204"/>
      <Path stroke="#000" d="M0-.5h204.002" transform="matrix(-1 .00421 -.00244 -1 1501 1247.29)"/>
      <Path stroke="#000" d="M1501 1380.5h-204m204 143h-204m204 143h-204m204 150.5h-204m-473.5 267v-708m.5 707.5h204"/>
      <Path stroke="#000" d="M0-.5h204.002" transform="matrix(1 -.00421 .00244 1 824 1945.71)"/>
      <Path stroke="#000" d="M824 1812.5h204m-204-143h204m-204-143h204M824 1376h204m-204.5 1V820m.5 556.5h204"/>
      <Path stroke="#000" d="M0-.5h204.002" transform="matrix(1 -.00421 .00244 1 824 1238.71)"/>
      <Path stroke="#000" d="M824 1105.5h204m-204-143h204m-204-143h204M823.5 2792v-708m.5 707.5h204"/>
      <Path stroke="#000" d="M0-.5h204.002" transform="matrix(1 -.00421 .00244 1 824 2653.71)"/>
      <Path stroke="#000" d="M824 2520.5h204m-204-143h204m-204-143h204M824 2084h204M.5 4039.58v-138m.5 137.5h204"/>
    </Svg>
  );
}