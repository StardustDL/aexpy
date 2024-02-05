<script setup lang="ts">
import { NIcon, NBreadcrumbItem } from 'naive-ui'
import { ReportIcon } from '../icons'
import { RouterLink } from 'vue-router'
</script>

<template>
    <n-breadcrumb-item>
        <router-link to="/reports">
            <n-icon>
                <ReportIcon />
            </n-icon>
            Report
        </router-link>
    </n-breadcrumb-item>
</template>