import { useSelector } from 'react-redux'
import axiosInstance from '../axios-instance'

function sendDataToServer(...data) {
  axiosInstance.post(
    `${process.env.REACT_APP_BACKEND_URL}/logs/`,
    { ...data },
    {
      withCredentials: true,
    }
  )
}

class EventLogger {
  constructor(initialContext = {}) {
    this.logEvents = (message, type, context) => {
      sendDataToServer({
        message,
        type,
        ...initialContext,
        ...context,
      })
    }
  }

  error(message, context) {
    return this.log('error', message, context)
  }

  alert(message, context) {
    return this.log('alert', message, context)
  }

  log(message, type, context = {}) {
    const timestamp = new Date().toISOString()
    return this.logEvents(message, type, { ...context, timestamp })
  }
}

/**
 * EventLogger that POSTs data to the Django API, abstracted as a React Hook.
 *
 * ex:
 * const logger = useEventLogger()
 * logger.error('Some strange error')
 */
export function useEventLogger() {
  const user = useSelector((state) => state.auth.user)
  return new EventLogger({ username: user.email })
}

/**
 * Alert logger that POSTs data to the Django API.
 *
 * @param message {string} - Error message to log.
 * @param context {Object} - Additional properties and context.
 *
 * A `timestamp` is automatically generated in the EventLogger.
 *
 * ex:
 * logAlertToServer('The user clicked the button!')
 */
export function logAlertToServer(message, context) {
  const logger = new EventLogger()
  return logger.alert(message, context)
}

/**
 * Error logger that POSTs data to the Django API.
 *
 * @param message {string} - Error message to log.
 * @param context {Object} - Additional properties and context.
 *
 * A `timestamp` is automatically generated in the EventLogger.
 *
 * ex:
 * logErrorToServer('Some strange error')
 */
export function logErrorToServer(message, context) {
  const logger = new EventLogger()
  return logger.error(message, context)
}
