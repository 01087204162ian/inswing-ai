module.exports = {
  apps: [{
    name: 'inswing-ai',
    script: 'app.py',
    interpreter: 'python3',
    cwd: '/home/ec2-user/inswing-ai',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    env: {
      FLASK_ENV: 'production'
    }
  }]
};
