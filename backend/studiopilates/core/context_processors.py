from . import models


def user_permissions(request):
    is_professor = False
    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        profissional = models.Profissional.objects.select_related("cdPerfilAcesso").filter(user=user).first()
        if profissional and profissional.cdPerfilAcesso_id:
            perfil = (profissional.cdPerfilAcesso.dsPerfilAcesso or "").strip().lower()
            is_professor = "professor" in perfil
    return {"is_professor": is_professor}
