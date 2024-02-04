<script setup lang="ts">
import { NIcon, NBreadcrumbItem } from 'naive-ui'
import { PreprocessIcon } from '../icons'
import { RouterLink } from 'vue-router'
</script>

<template>
    <n-breadcrumb-item>
        <router-link to="/distribution">
            <n-icon>
                <PreprocessIcon />
            </n-icon>
            Distribution
        </router-link>
    </n-breadcrumb-item>
</template>