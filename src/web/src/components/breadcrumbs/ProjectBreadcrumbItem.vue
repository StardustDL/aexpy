<script setup lang="ts">
import { NIcon, NBreadcrumbItem } from 'naive-ui'
import { ProjectIcon } from '../icons'
import { RouterLink } from 'vue-router'
</script>

<template>
    <n-breadcrumb-item>
        <router-link to="/projects">
            <n-icon :component="ProjectIcon" />
            Projects
        </router-link>
    </n-breadcrumb-item>
</template>