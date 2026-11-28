import { useEffect, useState } from 'react'

// Gọi loader một lần khi trang mở: loading → ready / error
export default function useApi(loader) {
  const [state, setState] = useState({ status: 'loading', data: null, error: null })

  useEffect(() => {
    let alive = true
    loader()
      .then(data => alive && setState({ status: 'ready', data, error: null }))
      .catch(error => alive && setState({ status: 'error', data: null, error }))
    return () => { alive = false }
  }, [loader])

  return state
}
