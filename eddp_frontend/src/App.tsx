import { RouterProvider } from 'react-router-dom'

import { AppErrorBoundary } from './components/common/ErrorBoundary'
import { appRouter } from './routes/router'

function App() {
  return (
    <AppErrorBoundary>
      <RouterProvider router={appRouter} />
    </AppErrorBoundary>
  )
}

export default App
