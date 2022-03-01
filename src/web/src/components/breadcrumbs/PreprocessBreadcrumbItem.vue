<script setup lang="ts">
import { NIcon, NBreadcrumbItem } from 'naive-ui'
import { PreprocessIcon } from '../icons'
import { RouterLink } from 'vue-router'
import { useStore } from '../../services/store'

const store = useStore();
</script>

<template>
    <n-breadcrumb-item>
        <router-link to="/preprocessing">
            <n-icon>
                <PreprocessIcon />
            </n-icon>
            Preprocess
        </router-link>
    </n-breadcrumb-item>
</template>