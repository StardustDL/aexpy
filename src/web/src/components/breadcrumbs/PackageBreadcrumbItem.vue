<script setup lang="ts">
import { NIcon, NBreadcrumbItem } from 'naive-ui'
import { PackageIcon } from '../icons'
import { RouterLink } from 'vue-router'
</script>

<template>
    <n-breadcrumb-item>
        <router-link to="/packages">
            <n-icon :component="PackageIcon" />
            Packages
        </router-link>
    </n-breadcrumb-item>
</template>