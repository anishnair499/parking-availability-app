import {View, Text, Image, ImageBackground, ScrollView} from "react-native"
const logoImg = require("../assets/images/react-logo.png")
export default function Index() {
 return (
 <View style = {{flex: 1, backgroundColor: "#2a2e33", padding:20}}>
  <ScrollView>
   <Image source = {logoImg} style = {{height:300, width:300}}/>
    <Text>
      Lorem ipsum dolor sit amet consectetur, adipisicing elit. Reprehenderit, placeat quia eos, magni veniam fuga, accusantium ex id rem maxime labore molestiae culpa voluptatibus aliquam velit est assumenda voluptates perspiciatis!
      Lorem ipsum dolor sit amet consectetur, adipisicing elit. Voluptates laboriosam dicta similique dolore sequi porro tenetur id magnam, quidem officiis quis ad nulla? Tempore consequuntur exercitationem sapiente enim quod ipsum!
      Lorem, ipsum dolor sit amet consectetur adipisicing elit. Commodi at delectus vel placeat enim esse! Eaque error beatae quo nam enim officiis asperiores? Dolorum blanditiis eius eum voluptatibus error perferendis!
      Lorem
    </Text>
    <Image source = {logoImg} style = {{height:300, width:300}}/>
  </ScrollView>
 </View>
 );
}
