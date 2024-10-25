WORK IN PROGRESS - DO NOT USE !


A simple OPNsense plugin that send Monit alerts to the telegram bot. All creds to kulikov-a. 

Mod version: added ipinfo.io token to retrieve ip information where available. To extend cache (to accommodate for longer message), add this to /usr/local/opnsense/service/templates/OPNsense/Monit/monitrc:

SET LIMITS {
   FILECONTENTBUFFER: 1 MB
}

--> see https://github.com/opnsense/core/commit/4d088ef5bdd6ebf1e963a178798c9e6e636992aa#diff-8bc0b45afd249a5e9ee38729f47cd8a7818ee6d40a9d876def5ab67fd91cc9a2R31

ref. https://forum.opnsense.org/index.php?topic=36805.0

![image](https://github.com/user-attachments/assets/14e34337-5785-47cb-927c-af1baf891453)

```pkg add https://github.com/kulikov-a/opn-monit2t/raw/main/work/pkg/<current-monit2t-ver.pkg>```
