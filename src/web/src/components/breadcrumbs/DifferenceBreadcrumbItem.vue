<script setup lang="ts">
import { NIcon, NBreadcrumbItem } from 'naive-ui'
import { DifferenceIcon } from '../icons'
import { RouterLink } from 'vue-router'
</script>

<template>
    <n-breadcrumb-item>
        <router-link to="/changes">
            <n-icon>
                <DifferenceIcon />
            </n-icon>
            Changes
        </router-link>
    </n-breadcrumb-item>
</template>