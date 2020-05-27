node {
    def microqImage
    stage('git') {
        checkout scm
    }
    stage('Test GUI') {
        sh "npm install"
        sh "npm update"
        sh "npm test"
    }
    stage('Build') {
        microqImage = docker.build("odinsmr/microq")
    }
    stage('Test') {
        sh "tox -- --runslow --runsystem"
    }
    stage('Cleanup') {
      sh "rm -r .tox"
    }
    if (env.BRANCH_NAME == 'master') {
      stage('push') {
        withDockerRegistry([ credentialsId: "dockerhub-molflowbot", url: "" ]) {
           microqImage.push(env.BUILD_TAG)
           microqImage.push('latest')
        }
      }
    }
}
