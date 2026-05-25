import { View, Text, StyleSheet, Switch } from "react-native";
import { useFonts } from "expo-font";
import * as React from "react";
import { useState } from "react";
import { colors } from "./styles/global";
export default function Settings() {
  const [isDark, setIsDark] = useState(false);

  const [fontsLoaded] = useFonts({
    "Montserrat-Bold": require("../assets/fonts/Montserrat-VariableFont_wght.ttf"),
  });

  if (!fontsLoaded) return null;

  return (
  <React.Fragment>
   <View style ={{flex: 1, backgroundColor: colors.background, justifyContent: "center", alignItems: "center"}}>
    <Text style = {{color: colors.text, fontSize: 24, fontFamily: "Montserrat-Bold",marginBottom: 200}}>
      Settings
    </Text>
   </View>
   <View style = {{flex: 1, backgroundColor: colors.background, justifyContent: "center", alignItems: "center"}}>
    <Text style = {{color: colors.text, fontSize: 18, fontFamily: "Montserrat-Bold", marginBottom: 10
    }}>Style</Text>
   </View>
  </React.Fragment>
  );
}

