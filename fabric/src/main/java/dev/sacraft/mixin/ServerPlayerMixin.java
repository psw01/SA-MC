package dev.sacraft.mixin;

import dev.sacraft.SACraft;
import dev.sacraft.combat.SkyCombat;
import dev.sacraft.combat.SAActorEntity;
import dev.sacraft.link.Proto;
import dev.sacraft.link.SkyLink;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.server.level.ServerPlayer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(ServerPlayer.class)
public abstract class ServerPlayerMixin {
	/** Critical hits on a SA actor are flagged so SA can play them up. */
	@Inject(method = "crit", at = @At("HEAD"))
	private void sacraft$critSA(Entity entity, CallbackInfo ci) {
		if (entity instanceof SAActorEntity proxy) {
			proxy.markCritical();
		}
	}

	/** Dying in Minecraft is dying in SA: the host's through the link, a guest's through theirs. */
	@Inject(method = "die", at = @At("HEAD"))
	private void sacraft$diesInSA(DamageSource source, CallbackInfo ci) {
		ServerPlayer self = (ServerPlayer) (Object) this;
		int attacker = SkyCombat.attackerEntityIndex(source);
		if (!dev.sacraft.net.SkyNet.isHost(self)) {
			if (net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking.canSend(self, dev.sacraft.net.SkyNet.Died.TYPE)) {
				net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking.send(self, new dev.sacraft.net.SkyNet.Died(attacker));
			}
			SACraft.LOG.info("SACraft: guest {} died ({}); telling their SA", self.getPlainTextName(), source.getMsgId());
			return;
		}
		if (SkyLink.active()) {
			SkyLink.pushEvent(Proto.EV_PLAYER_DIED, attacker, 0, 0, 0, 0, 0);
			SACraft.LOG.info("SACraft: player died ({}); telling SA", source.getMsgId());
		}
	}
}
