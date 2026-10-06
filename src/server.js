import app from './app.js';
import config from './config.js';

const server = app.listen(config.port, () => {
  console.log(`${config.appName} listening on http://localhost:${config.port}`);
});

export default server;
