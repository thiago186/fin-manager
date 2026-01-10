import { useDark, useToggle } from '@vueuse/core'

export const useTheme = () => {
  const isDark = useDark({
    storageKey: 'theme',
    selector: 'html',
    attribute: 'class',
    valueDark: 'dark',
    valueLight: '',
  })

  const toggle = useToggle(isDark)

  const setDark = () => {
    isDark.value = true
  }

  const setLight = () => {
    isDark.value = false
  }

  return {
    isDark,
    toggle,
    setDark,
    setLight,
  }
}

