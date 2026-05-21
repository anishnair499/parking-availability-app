import {View, Text, Image, ImageBackground, ScrollView, StyleSheet, Button} from "react-native"
const logoImg = require("../assets/images/react-logo.png")
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#2a2e33",
    padding: 20,
  },
  text: {
    fontSize: 30,
    color: "#fff",
    textAlign: "center",
    fontFamily: "Corptica-Bold",
  },
  button: {
    padding:10,
    width: 100,
    backgroundColor: "#fff",
    borderRadius: 5,
    marginTop: 20,
    }
});
export default function Index( {navigation}: any) {
 return (
 <View style = {styles.container}>
  <Text style = {styles.text}>
    LotLink
  </Text> 
  <View style={styles.button}>
    <Button onPress={() => navigation.navigate("Settings")} title="Settings" />
  </View>
 </View>
 );
}