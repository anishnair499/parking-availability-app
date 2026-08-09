import { colors, globalStyles } from "./styles/global"
import {View, Text, Image, ImageBackground, ScrollView, Button} from "react-native"
import Svg, { Line, Rect, Image as SvgImage } from 'react-native-svg';
const logoImg = require("../assets/images/IMG_9026-removebg-preview.png")
const carImg = require("/Users/sarvad/parking-availability-app/frontend/assets/images/indexCar.jpeg")
export default function Index() {
 return (
  <ScrollView>
 <View style = {{flex: 1,backgroundColor: colors.background, justifyContent: "flex-start", alignItems: "center"}}>

    <Image source={logoImg} style={{ width: 300, height: 150, marginTop:30 }}/>
  
    <View style={{...globalStyles.box,width:900,height:700}}>
        <Text style = {{...globalStyles.primaryText}}>
            Welcome To Lotlink. 
        </Text>
        
        <Text style = {{...globalStyles.secondaryText}}>
          Parking Availiability. Anywhere. Anytime.
          
        </Text>
        
        <Svg height = "250">
        <Line x1 = "320" y1 = "30" x2 = "550" y2 = "30" stroke = "black" strokeWidth= "2"/>
        <SvgImage x="500" y="40" width="150" height="200" href={carImg}/>
        
        </Svg>
          <View style = {{borderWidth: 2, borderColor: "green", width: 1000, height: 300, alignSelf: 'flex-start' }}> 
          <Text style = {{flexShrink: 1, textAlign: "center", marginRight: 300}}>asdfasdfsd</Text>
      </View>
    </View>
  </View>
 </ScrollView>
 );
}