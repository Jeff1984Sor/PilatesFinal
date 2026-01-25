from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify

from .models import PerfilAcesso, Profissional


def _get_default_perfil():
    perfil, _ = PerfilAcesso.objects.get_or_create(cdPerfilAcesso=1, defaults={"dsPerfilAcesso": "Padrao"})
    return perfil


def _next_cd_profissional():
    max_cd = Profissional.objects.order_by("-cdProfissional").values_list("cdProfissional", flat=True).first() or 0
    return max_cd + 1


def ensure_profissional_for_user(user):
    if getattr(user, "_syncing_profissional", False):
        return None
    nome = (user.get_full_name() or user.first_name or user.username or "").strip()
    if not nome:
        nome = f"Usuario {user.pk}"
    profissional = Profissional.objects.filter(user=user).first()
    if not profissional:
        profissional = Profissional.objects.create(
            cdProfissional=_next_cd_profissional(),
            profissional=nome,
            cdPerfilAcesso=_get_default_perfil(),
            user=user,
        )
        return profissional
    if nome and profissional.profissional != nome:
        profissional.profissional = nome
        profissional.save(update_fields=["profissional"])
    return profissional


@receiver(post_save, sender=get_user_model())
def _sync_profissional_on_user_save(sender, instance, **kwargs):
    ensure_profissional_for_user(instance)


@receiver(post_save, sender=Profissional)
def _sync_user_on_profissional_save(sender, instance, **kwargs):
    if getattr(instance, "_syncing_user", False):
        return
    User = get_user_model()
    if instance.user_id:
        user = instance.user
        if getattr(user, "_syncing_profissional", False):
            return
        desired_name = (instance.profissional or "").strip()
        if desired_name and user.first_name != desired_name:
            user._syncing_profissional = True
            try:
                user.first_name = desired_name
                user.save(update_fields=["first_name"])
            finally:
                user._syncing_profissional = False
        return
    base_username = slugify(instance.profissional) or f"user-{instance.pk}"
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        counter += 1
        username = f"{base_username}-{counter}"
    user = User(username=username, first_name=instance.profissional)
    user.set_unusable_password()
    user._syncing_profissional = True
    user.save()
    instance._syncing_user = True
    try:
        instance.user = user
        instance.save(update_fields=["user"])
    finally:
        instance._syncing_user = False
