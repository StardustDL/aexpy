<script setup lang="ts">
import { NIcon, NBreadcrumbItem } from 'naive-ui'
import { DistributionIcon } from '../icons'
import { RouterLink } from 'vue-router'
</script>

<template>
    <n-breadcrumb-item>
        <router-link to="/distributions">
            <n-icon :component="DistributionIcon" />
            Distributions
        </router-link>
    </n-breadcrumb-item>
</template>