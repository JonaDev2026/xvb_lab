import os

from core.config import leggi_config
from core.playlists import (
    categorie_m3u, leggi_lista, liste_in_cartella, nome_vista
)
from core.epg import leggi_epg, prendi_epg, unisci_guide
from core.favorites import leggi_preferiti_cat


class Sessione:
    def __init__(self):
        self.config = leggi_config()
        self.liste = []
        self.canali = []
        self.epg_nomi = {}
        self.epg = {}
        self.preferiti = []
        self.carica_liste()
        self.carica_preferiti()

    def carica_liste(self):
        configurate = self.config.get("liste", [])
        if isinstance(configurate, str):
            configurate = [configurate]
        viste = set()
        for percorso in configurate:
            if not isinstance(percorso, str) or not percorso or percorso in viste:
                continue
            viste.add(percorso)
            if percorso.startswith(("http://", "https://")):
                try:
                    canali = leggi_lista(percorso)
                except Exception:
                    canali = []
            else:
                if not os.path.isfile(percorso):
                    continue
                try:
                    canali = leggi_lista(percorso)
                except Exception:
                    canali = []
            categorie = categorie_m3u(percorso)
            voce = {
                "percorso": percorso,
                "nome": nome_vista(percorso),
                "canali": canali,
                "categorie": categorie,
            }
            self.liste.append(voce)
            for nome, url, ide in canali:
                self.canali.append((nome, url, ide, categorie.get(url, "Altri"), percorso))
        if not configurate:
            for percorso in liste_in_cartella():
                try:
                    canali = leggi_lista(percorso)
                    categorie = categorie_m3u(percorso)
                except Exception:
                    continue
                self.liste.append({
                    "percorso": percorso, "nome": nome_vista(percorso),
                    "canali": canali, "categorie": categorie,
                })
                for nome, url, ide in canali:
                    self.canali.append((nome, url, ide, categorie.get(url, "Altri"), percorso))


    def carica_preferiti(self):
        try:
            self.preferiti = leggi_preferiti_cat()
        except Exception:
            self.preferiti = []
        for nome, url, ide, categoria in self.preferiti:
            self.canali.append((nome, url, ide, categoria or "MyPlaylist", "__favorite__"))

    def carica_guide(self):
        guide = []
        percorsi = self.config.get("epg", [])
        if isinstance(percorsi, str):
            percorsi = [percorsi] if percorsi else []
        for percorso in percorsi:
            try:
                guide.append(leggi_epg(prendi_epg(percorso)))
            except Exception:
                continue
        if guide:
            self.epg_nomi, self.epg = unisci_guide(guide)

    def categorie(self, percorso=None):
        nomi = set()
        for lista in self.liste:
            if percorso is None or lista["percorso"] == percorso:
                nomi.update(lista["categorie"].values())
        return sorted(nomi, key=str.casefold)

    def canali_per(self, percorso=None, categoria=None, ricerca=""):
        q = (ricerca or "").casefold()
        return [
            voce for voce in self.canali
            if (percorso is None or voce[4] == percorso)
            and (categoria is None or voce[3] == categoria)
            and (not q or q in voce[0].casefold())
        ]
