import {NavigationContainer, NavigationIndependentTree} from "@react-navigation/native"
import {createNativeStackNavigator} from "@react-navigation/native-stack"
import Index from "./index"
import Settings from "./settings"

const Stack = createNativeStackNavigator()

export default function App() {
  return (
  <NavigationIndependentTree>
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Index">
        <Stack.Screen name="Index" component={Index} />
        <Stack.Screen name="Settings" component={Settings} />
      </Stack.Navigator>
    </NavigationContainer>
  </NavigationIndependentTree>
  )
}