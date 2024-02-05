<script setup lang="ts">
import { NIcon, NBreadcrumbItem } from 'naive-ui'
import { DescriptionIcon } from '../icons'
import { RouterLink } from 'vue-router'
</script>

<template>
    <n-breadcrumb-item>
        <router-link to="/apis">
            <n-icon>
                <DescriptionIcon />
            </n-icon>
            APIs
        </router-link>
    </n-breadcrumb-item>
</template>