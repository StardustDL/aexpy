<script setup lang="ts">
import { NIcon, NBreadcrumbItem } from 'naive-ui'
import { HomeIcon } from '../icons'
import { RouterLink } from 'vue-router'
</script>

<template>
    <n-breadcrumb-item>
        <router-link to="/">
            <n-icon :component="HomeIcon" />
            AexPy
        </router-link>
    </n-breadcrumb-item>
</template>