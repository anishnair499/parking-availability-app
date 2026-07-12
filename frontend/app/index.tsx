import { colors, globalStyles } from "./styles/global"
import {View, Text, Image, ImageBackground, ScrollView, Button} from "react-native"
const logoImg = require("../assets/images/IMG_9026-removebg-preview.png")
export default function Index( {navigation}: any) {
 return (
 <View style = {{flex: 1,backgroundColor: colors.background}}>
  <View style = {{justifyContent: "flex-start", alignItems: "center", flex: 1}}>
    <Image source={logoImg} style={{ width: 300, height: 150, marginTop:30 }}/>
  <View style = {{}}>
    <View style={{...globalStyles.box,width:900,height:700}}>
        <Text style = {{...globalStyles.primaryText}}>
            Welcome To Lotlink. 
        </Text>
        <Text style = {{...globalStyles.secondaryText}}>
          Parking Availiability. Anywhere. Anytime
          
        </Text>
    </View>
    </View>
  </View>
 </View>
 );
}