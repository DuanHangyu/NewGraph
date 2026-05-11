import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import History from '../views/History.vue'
import Process from '../views/Process.vue'
import Classroom from '../views/Classroom.vue'
import ProjectWorkbench from '../views/ProjectWorkbench.vue'
import QA from '../views/QA.vue'
import QAGraph from '../views/QAGraph.vue'
import DatasetManager from '../views/DatasetManager.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/history',
    name: 'History',
    component: History
  },
  {
    path: '/process/:projectId',
    name: 'Process',
    component: Process,
    props: true
  },
  {
    path: '/workbench/:projectId',
    name: 'Workbench',
    component: ProjectWorkbench,
    props: true
  },
  {
    path: '/classroom/:classroomId',
    name: 'Classroom',
    component: Classroom,
    props: true
  },
  {
    path: '/qa/:projectId',
    name: 'QA',
    component: QAGraph,
    props: true
  },
  {
    path: '/qa-simple/:projectId',
    name: 'QASimple',
    component: QA,
    props: true
  },
  {
    path: '/datasets',
    name: 'Datasets',
    component: DatasetManager
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
