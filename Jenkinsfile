pipeline{
    agent any
    stages{
    
        stage('checkout'){
            steps{
                checkout scm
            }
        }
        stage('build'){
            steps{
                sh '''
                    echo "Building the project"
                    docker compose up --build -d
                '''
            }
        }
    }
    post {
    always {
        sh 'docker compose down -v --remove-orphans || true'
        cleanWs()
        }
    }
}