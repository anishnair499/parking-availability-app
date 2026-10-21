import { colors, globalStyles } from "../components/styles/global"
import  {View, Text, Image, ImageBackground, ScrollView, Button, Pressable, Alert} from "react-native"
import {useNavigation} from '@react-navigation/native';
import {useRouter} from "expo-router";
import Svg, { Line, Rect, Image as SvgImage } from 'react-native-svg';
import Parking from "./parking";
const logoImg = require("../assets/images/IMG_9026-removebg-preview.png")
const carImg = require("../assets/images/indexCar.jpeg")
export default function Index() {
  const router = useRouter();
 return (
  <ScrollView>
 <View style = {{flex: 1,backgroundColor: "#171C2B", justifyContent: "flex-start", alignItems: "center"}}>

    <Image source={logoImg} style={{width:150,height: 75,marginTop:40}}/>
  
    <View style={{...globalStyles.box,width:900,height:700, backgroundColor: "#171C2B"}}>
        <Text style = {{...globalStyles.primaryText, color:"white"}}>
            Welcome To LotLink. 
        </Text>
        
        <Text style = {{...globalStyles.secondaryText}}>
          Parking Availiability. Anywhere. Anytime.
          
        </Text>
        
        <Svg height = "250">
        <Line x1 = "320" y1 = "30" x2 = "550" y2 = "30" stroke = "black" strokeWidth= "2"/>
        
        </Svg>
          <View style = {{backgroundColor: '#2A2E33', boxShadow: '5px 6px 4px rgba(12, 12, 12, 0.2)',borderRadius: 20, borderWidth: 1.5, marginLeft: 260,marginTop: -200, borderColor: "black", width: 350, height: 200, alignSelf: 'flex-start' }}>
            <Text style = {{...globalStyles.primaryText, marginTop:20, color: "black", fontFamily: "Montserrat"}}>
              Find 
              Parking
            </Text>
            <Button title = "Find Parking" onPress={() => router.navigate("/parking")}/>
          </View>
          

    </View>
    <Button title = "Find Parking Now"></Button>
  </View>
 </ScrollView>
 );
}