import { View, Text, Image} from "react-native"
import { colors } from "./styles/global"
const parkingImg = require("../assets/images/parking.jpg") 
export default function Parking() { 
    return (
        <View style={{ flex: 1, backgroundColor: colors.background, justifyContent: "center", alignItems: "center" }}>
            <Image source={parkingImg} style={{ aspectRatio: 2/3, width: 500,height:250, transform: [{ rotate: '90deg' }] }} />
        </View>
    )
}