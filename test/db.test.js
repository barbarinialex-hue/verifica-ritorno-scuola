export class AppError extends Error {
  constructor(statusCode, code, message, details = null) {
    super(message);
    this.name = 'AppError';
    this.statusCode = statusCode;
    this.code = code;
    this.details = details;
  }
}

export function notFoundHandler(req, res) {
  res.status(404).json({
    success: false,
    error: {
      code: 'NOT_FOUND',
      message: `Route not found: ${req.method} ${req.originalUrl}`,
    },
  });
}

export function errorHandler(err, req, res, next) {
  if (res.headersSent) {
    return next(err);
  }

  const statusCode = err.statusCode ?? 500;
  const code = err.code ?? 'INTERNAL_SERVER_ERROR';
  const message = err.message ?? 'Unexpected server error.';

  const response = {
    success: false,
    error: {
      code,
      message,
    },
  };

  if (err.details) {
    response.error.details = err.details;
  }

  if (statusCode >= 500 && process.env.NODE_ENV !== 'production') {
    response.error.stack = err.stack;
  }

  res.status(statusCode).json(response);
}
