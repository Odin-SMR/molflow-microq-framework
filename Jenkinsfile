node {
    checkout scm
    stage('Test GUI') {
        sh "npm install"
        sh "npm update"
        sh "npm test"
    }
    stage('Test') {
        sh "tox -- --runslow --runsystem"
    }
    stage('Build') {
        sh "docker build -t docker2.molflow.com/devops/microq ."
    }
    stage("Push") {
        if (env.GIT_BRANCH == 'origin/master') {
            sh "docker push docker2.molflow.com/devops/microq"
        }
    }
}
