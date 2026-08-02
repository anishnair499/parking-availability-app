import {NavigationContainer, NavigationIndependentTree} from "@react-navigation/native"
import {createNativeStackNavigator} from "@react-navigation/native-stack"
import { colors } from "./styles/global"
import { Ionicons } from "@expo/vector-icons"
import { Tabs } from "expo-router"
import Index from "./index"
import Settings from "./settings"

const Stack = createNativeStackNavigator()

export default function App() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        headerStyle: { backgroundColor: colors.header },
        headerTintColor: colors.text,
        tabBarStyle: { backgroundColor: colors.header },
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textSecondary,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Home",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home" color={color} size={size} />
          ),
        }}  
      />
      <Tabs.Screen
       name="parking"
       options={{
        title: "Parking",
        tabBarIcon: ({ color, size }) => (
          <Ionicons name="car" color={color} size={size} />
        ),
       }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: "Settings",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="settings" color={color} size={size} />
          ),
        }}  
      />
      
    </Tabs>
  )
}