<script setup lang="ts">
import { NIcon, NBreadcrumbItem } from 'naive-ui'
import { CodeIcon } from '../icons'
import { RouterLink } from 'vue-router'
import { useStore } from '../../services/store'

const store = useStore();
</script>

<template>
    <n-breadcrumb-item>
        <router-link to="/coding">
            <n-icon>
                <CodeIcon />
            </n-icon>
            Code
        </router-link>
    </n-breadcrumb-item>
</template>