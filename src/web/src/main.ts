import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { store, key } from './services/store'

import App from './App.vue'
import Home from './pages/Home.vue'
import DistributionView from './pages/view/Distribution.vue'
import DescriptionView from './pages/view/Description.vue'
import DifferenceView from './pages/view/Difference.vue'
import ReportView from './pages/view/Report.vue'
import PackageView from './pages/view/Package.vue'
import NotFound from './pages/NotFound.vue'
import { publicModels } from './services/utils'

const routes = [
    {
        path: '/',
        component: Home,
        meta: {
            title: 'Home'
        }
    },
    {
        path: '/distributions',
        component: Home,
        meta: {
            title: 'Home'
        }
    },
    {
        path: '/apis',
        component: Home,
        meta: {
            title: 'Home'
        }
    },
    {
        path: '/changes',
        component: Home,
        meta: {
            title: 'Home'
        }
    },
    {
        path: '/reports',
        component: Home,
        meta: {
            title: 'Home'
        }
    },
    {
        path: '/packages',
        component: Home,
        meta: {
            title: 'Home'
        }
    },
    {
        path: '/distributions/:id',
        component: DistributionView,
        meta: {
            title: 'Distributions'
        }
    },
    {
        path: '/apis/:id',
        component: DescriptionView,
        meta: {
            title: 'APIs'
        }
    },
    {
        path: '/changes/:id',
        component: DifferenceView,
        meta: {
            title: 'Changes'
        }
    },
    {
        path: '/reports/:id',
        component: ReportView,
        meta: {
            title: 'Reports'
        }
    },
    {
        path: '/packages/:id',
        component: PackageView,
        meta: {
            title: 'Packages'
        }
    },
    {
        path: '/:path*',
        component: NotFound,
        meta: {
            title: 'Not Found'
        }
    }
];

const router = createRouter({
    history: createWebHistory(),
    routes: routes,
})

router.beforeEach((to, from) => {
    if (to.path == from.path) {
        return true;
    }
    let params = <{
        id?: string,
    }>to.params;
    let title = (to.meta.title as any).toString() + " - AexPy";
    if (params.id) {
        title = `${params.id} - ${title}`;
    }
    document.title = title;
    return true;
});

const app = createApp(App);
app.use(router).use(store, key);

app.mount('#app')

publicModels();
