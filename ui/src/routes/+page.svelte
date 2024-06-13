<script lang="ts">
	import MenuBar from '$lib/components/MenuBar.svelte';
	import Devices from '$lib/components/Devices.svelte';
	import TopologyMonitor from '$lib/components/TopologyMonitor.svelte';

	let sidePanelPosition = 'left'; // Change this to 'right' to move the side panel
</script>

<MenuBar title="Thread Network Manager" />

<div class="content {sidePanelPosition}">
	<Devices position={sidePanelPosition} width="400px" />

	<TopologyMonitor />
</div>

<style>
	.content {
		display: flex;
	}
	.side-panel-placeholder {
		width: 200px;
	}
	.main-content {
		flex-grow: 1;
		padding: 20px;
	}
	.content.left .main-content {
		margin-left: 200px;
	}
	.content.right .main-content {
		margin-right: 200px;
	}
</style>
