import { View, Text, StyleSheet, Switch } from "react-native";
import { useFonts } from "expo-font";
import * as React from "react";
import { useState } from "react";
import { colors } from "./styles/global";
import {globalStyles} from "./styles/global"
export default function Settings() {
  const [isDark, setIsDark] = useState(false);

  const [fontsLoaded] = useFonts({
    "Montserrat-Bold": require("../assets/fonts/Montserrat-VariableFont_wght.ttf"),
  });

  if (!fontsLoaded) return null;

  return (
  <React.Fragment>
   <View style ={{flex: 1, backgroundColor: colors.background, justifyContent: "center", alignItems: "center"}}>
    <Text style = {{...globalStyles.primaryText, marginBottom: 550, fontSize: 40}}>
      Settings
    </Text>
   </View>
   
  </React.Fragment>
  );
}

