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
                    docker compose up --build 
                '''
            }
        }
    }
}